import re
import json
import spacy
from spacy.matcher import PhraseMatcher
from rapidfuzz import process, fuzz
from typing import List, Optional, Dict
from app.schemas.user import UserProfile, FinalUserProfile, ResumeEntry
from app.utils.resume_parser import extract_text
from app.utils.skills import nlp, SKILLS_DB, TECH_WHITELIST, SOFT_SKILL_KEYWORDS, hybrid_tech_extraction

# Robust Section Header Mapping
SECTION_MAP = {
    "EDUCATION": ["Education", "Academic Background", "Educational Qualification", "Qualification", "Academic Details"],
    "EXPERIENCE": ["Work Experience", "Professional Experience", "Relevant Experience", "Work History", "Internships", "Experience", "Summary of Work","Leadership Experience"],
    "SKILLS": ["Skills", "Technical Skills", "Key Skills", "Core Competencies", "Technologies", "Expertise", "Skill Highlights", "Soft Skills"],
    "PROJECTS": ["Projects", "Personal Projects", "Academic Projects", "Key Projects", "Portfolio", "Recent Work"],
    "CERTIFICATIONS": ["Certifications", "Certificates", "Awards", "Honors", "Achievements"],
    "SUMMARY": ["Summary", "Profile", "Professional Summary", "Career Objective", "About Me", "Overview"],
    "LANGUAGES": ["Languages", "Linguistics"],
    "INTERESTS": ["Interests", "Hobbies", "Extra-curricular Activities"]
}

# Add sections to exclusion list to prevent header-name hallucination
SECTION_HEADERS = {v.lower() for sub in SECTION_MAP.values() for v in sub}

INDIAN_LOCATIONS = ["Madhya Pradesh", "Bhopal", "India", "M.P", "M.P.", "Delhi", "Mumbai", "Pune", "Gandhinagar", "Sagar", "Indore", "Uttar Pradesh", "Bihar"]

def clean_text(text: str) -> str:
    """Normalize text and handles CID font issues and spacing patterns."""
    text = re.sub(r'\(cid:\d+\)', '', text)
    
    def rejoin_spaced(match):
        return match.group(0).replace(' ', '')
    
    # Identify patterns where letters (any case) are separated by spaces (e.g. O m A n a n d)
    text = re.sub(r'(?:[A-Za-z]\s){2,}[A-Za-z]', rejoin_spaced, text)
    
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def get_sections(raw_text: str) -> Dict[str, str]:
    """Fuzzy header state-machine to identify sections and prevent bleed."""
    lines = [l.strip() for l in raw_text.split('\n')]
    sections = {"TOP": ""}
    current_section = "TOP"
    
    header_to_canonical = {}
    all_variations = []
    for canonical, variations in SECTION_MAP.items():
        for v in variations:
            low_v = v.lower()
            all_variations.append(low_v)
            header_to_canonical[low_v] = canonical

    for line in lines:
        if not line:
            continue
            
        # Check if line looks like a header
        if len(line) < 35:
            match = process.extractOne(line.lower(), all_variations, scorer=fuzz.token_set_ratio)
            if match and match[1] > 85:
                # To ensure it isn't just a skill name (e.g., "Java" in a list)
                if len(line) <= len(match[0]) + 10:
                    current_section = header_to_canonical[match[0]]
                    if current_section not in sections:
                        sections[current_section] = ""
                    continue
        
        sections[current_section] += line + "\n"
        
    return sections

def extract_name(text: str) -> Optional[str]:
    """Strict Name Extraction: Strips noise (Phone/Email) before evaluating candidates."""
    # Restricted window to first header
    snippet = text[:300]
    
    # Exclusion List (Tech, Locations, Section Headers)
    exclusion_list = TECH_WHITELIST.union({loc.lower() for loc in INDIAN_LOCATIONS})
    exclusion_list.update(SECTION_HEADERS)
    exclusion_list.update({sk.lower() for sk in SOFT_SKILL_KEYWORDS})
    exclusion_list.update({"resume", "curriculum", "skill", "projects", "education", "experience", "profile"})

    # 1. Primary: Use spaCy NER PERSON on cleaned text
    doc = nlp(snippet)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            candidate = ent.text.strip()
            if len(candidate.split()) >= 2 and candidate.lower() not in exclusion_list:
                # Discard if it contains digits (probably a mis-identified address/phone)
                if not any(d.isdigit() for d in candidate):
                    return candidate
                    
    # 2. Advanced Fallback: Clean lines and look for Capitalized Word sequences
    lines = [l.strip() for l in snippet.split('\n') if l.strip()]
    for line in lines[:5]:
        # Strip phone, email, and URL noise to expose the name
        clean_l = re.sub(r'[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}', '', line) # Email
        clean_l = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+91[-\s]?\d{10}|[6-9]\d{9}', '', clean_l) # Phone
        clean_l = re.sub(r'http\S+|www\S+', '', clean_l) # URL
        clean_l = clean_l.strip('. ,-_/')
        
        if not clean_l:
            continue

        # Look for sequences of 2+ Title Case words
        matches = re.findall(r'\b[A-Z][a-z]+\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', clean_l)
        if matches:
            for candidate in matches:
                if candidate.lower() not in exclusion_list:
                    return candidate
            
    return None

def extract_structured_entries(section_text: str, is_project: bool = True) -> List[ResumeEntry]:
    """Robust state-machine for projects: Strictly separates titles from descriptions."""
    if not section_text:
        return []
        
    lines = [l.strip() for l in section_text.split('\n') if l.strip()]
    entries = []
    current_entry = None
    
    TITLE_INDICATORS = ["System", "App", "Hackathon", "Website", "Dashboard", "Visualizer", "Tracker", "Platform", "Engine"]
    DESC_VERBS = ["Designed", "Built", "Implemented", "Created", "Gained", "Developed", "Integrated", "Managed", "Applied"]

    for line in lines:
        clean_l = line.strip('• -* \n')
        if not clean_l: continue

        # DETECTION RULES:
        # 1. A title MUST start with an Uppercase letter.
        # 2. A title MUST NOT end in a period.
        # 3. A title MUST NOT start with a common description verb (unless it's the very first line).
        is_sep = '|' in line or '–' in line
        has_indicator = any(ind in line for ind in TITLE_INDICATORS)
        starts_with_upper = clean_l[0].isupper() if clean_l else False
        ends_with_period = clean_l.endswith('.')
        starts_with_verb = any(v in clean_l[:15] for v in DESC_VERBS)
        is_bullet = line.startswith(('•', '-', '*'))

        # A title is identified if it has a separator OR (it has a title indicator AND starts capitalized AND doesn't end in a period).
        # We also override if it's the very first project line and no entry exists.
        is_title = (is_sep or (has_indicator and starts_with_upper and not ends_with_period)) and not (is_bullet and starts_with_verb)

        if (is_title and not starts_with_verb) or not current_entry:
            current_entry = ResumeEntry()
            if '|' in clean_l:
                parts = clean_l.split('|')
                current_entry.organization = parts[0].strip()
                current_entry.title = parts[1].strip()
            elif '–' in clean_l:
                parts = clean_l.split('–')
                current_entry.organization = parts[0].strip()
                current_entry.title = parts[1].strip()
            else:
                current_entry.title = clean_l
            
            entries.append(current_entry)
        else:
            # Bullet point or descriptive text
            current_entry.description.append(clean_l)

    # Re-map Tech Stack using the strict whitelist against entry text
    for entry in entries:
        context = entry.title + " " + " ".join(entry.description)
        entry.tech_stack = hybrid_tech_extraction(context, is_soft_skills=False)
        
    return entries

def extract_mail(text: str) -> Optional[str]:
    email_pattern = r'[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else None

def extract_phone(text: str) -> Optional[str]:
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+91[-\s]?\d{10}|[6-9]\d{9}'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else None

# Delegated extraction helpers
def extract_education(section_text: str) -> List[str]:
    if not section_text: return []
    lines = section_text.split('\n')
    filtered = []
    for line in lines:
        l_low = line.lower()
        if "skills" in l_low or "projects" in l_low: break
        if len(line.strip()) > 8: filtered.append(line.strip())
    return filtered

def extract_experience(section_text: str) -> List[ResumeEntry]:
    return extract_structured_entries(section_text, is_project=False)

def extract_projects(section_text: str) -> List[ResumeEntry]:
    return extract_structured_entries(section_text, is_project=True)

async def parse_resume(file_path: str) -> UserProfile:
    """
    Parse resume using Gemini for high-accuracy structured extraction.
    """
    from app.utils.ai_handler import AIHandler
    
    raw_text = extract_text(file_path)
    if not raw_text:
        return UserProfile()
        
    cleaned_raw = clean_text(raw_text)
    
    system_prompt = """
    You are an Expert Resume Parser. Extract all details from the provided resume text into a structured JSON format.
    Ensure you capture:
    - Personal details (name, email, phone, address, summary)
    - Experience (list of entries with title, organization, duration, description as list of points, tech_stack as list of strings)
    - Projects (list of entries with title, organization/context, duration, description as list of points, tech_stack as list of strings)
    - Education (list of strings)
    - Skills (technical) and Soft Skills
    - Languages, Certifications, Interests
    """
    
    prompt = f"""
    Raw Resume Text:
    {cleaned_raw[:15000]}
    
    Return the data as a JSON object matching this structure:
    {{
        "name": "string",
        "email": "string",
        "phone": "string",
        "address": "string",
        "summary": "string",
        "experience": [{{ "title": "...", "organization": "...", "duration": "...", "description": ["...", "..."], "tech_stack": ["...", "..."] }}],
        "projects": [{{ "title": "...", "organization": "...", "duration": "...", "description": ["...", "..."], "tech_stack": ["...", "..."] }}],
        "skills": ["...", "..."],
        "soft_skills": ["...", "..."],
        "education": ["...", "..."],
        "certifications": ["...", "..."],
        "languages": ["...", "..."],
        "interests": ["...", "..."]
    }}
    """
    
    try:
        # Use Gemini for superior context handling in resumes
        result_text = await AIHandler.generate_content(
            prompt=prompt,
            system_prompt=system_prompt,
            provider="gemini"
        )
        
        # Extract JSON from text
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(result_text)
        
        # RESILIENCE: Sanitize nested entries to prevent NoneType validation errors
        for entry_type in ["experience", "projects"]:
            if entry_type in data and isinstance(data[entry_type], list):
                for entry in data[entry_type]:
                    if isinstance(entry, dict):
                        if entry.get("title") is None: entry["title"] = "Unknown Role"
                        if entry.get("organization") is None: entry["organization"] = "Unknown Organization"
                        if entry.get("duration") is None: entry["duration"] = "N/A"
                        if not isinstance(entry.get("description"), list): entry["description"] = []
                        if not isinstance(entry.get("tech_stack"), list): entry["tech_stack"] = []

        # Validate and normalize
        return UserProfile(**data)
    except Exception as e:
        print(f"Resume parsing failed, falling back to basic extraction: {e}")
        # Fallback to a very basic structure if AI fails
        return UserProfile(
            name="Extraction Error",
            summary=f"Error: {str(e)}"
        )

def create_final_profile(user_profile: UserProfile) -> FinalUserProfile:
    return FinalUserProfile(
        name=user_profile.name or "Unknown Candidate",
        email=user_profile.email or "unknown@example.com",
        age=user_profile.age,
        phone=user_profile.phone or "N/A",
        address=user_profile.address or "Address Not Provided",
        experience=user_profile.experience,
        education=user_profile.education,
        certifications=user_profile.certifications,
        languages=user_profile.languages,
        summary=user_profile.summary,
        skills=user_profile.skills,
        soft_skills=user_profile.soft_skills,
        interests=user_profile.interests,
        projects=user_profile.projects
    )