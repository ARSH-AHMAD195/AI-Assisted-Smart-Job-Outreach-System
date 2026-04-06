import re
import spacy
from spacy.matcher import PhraseMatcher
from rapidfuzz import process, fuzz
from typing import List, Optional, Dict
from app.schemas.user import UserProfile, FinalUserProfile, ResumeEntry
from app.utils.resume_parser import extract_text

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")

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

# Categorized Skills Database (The master whitelist)
SKILLS_DB = {
    "Languages": ["Python", "Java", "C++", "C", "JavaScript", "TypeScript", "SQL", "HTML", "CSS", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin"],
    "Frontend": ["React", "Angular", "Vue", "Next.js", "Tailwind CSS", "Bootstrap", "Svelte", "Redux", "Vite", "jQuery", "UI/UX"],
    "Backend": ["FastAPI", "Django", "Flask", "Node.js", "Express.js", "Spring Boot", "Laravel", "Postman", "GraphQL", "REST API"],
    "DevOps/Cloud": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Jenkins", "Terraform", "Linux", "CI/CD", "Prometheus"],
    "Data/AI": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "NumPy", "Pandas", "Scikit-learn", "OpenCV", "Face Recognition", "R Language", "Spark"],
    "Databases": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite", "Oracle", "Cassandra", "Elasticsearch", "Prisma"]
}

# Flattened Whitelist for strict validation
TECH_WHITELIST = {skill.lower() for cat in SKILLS_DB.values() for skill in cat}
# Soft Skills for mapping
SOFT_SKILL_KEYWORDS = ["Communication", "Teamwork", "Problem Solving", "Leadership", "Presentation", "Self-Learning", "Time Management", "Collaboration", "Decision Making", "Adaptability"]
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

def hybrid_tech_extraction(text: str, is_soft_skills: bool = False) -> List[str]:
    """Extracts tech stack strictly against the TECH_WHITELIST."""
    found = set()
    
    if is_soft_skills:
        # Soft Skills detection
        for sk in SOFT_SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(sk) + r'\b', text, re.IGNORECASE):
                found.add(sk)
        return sorted(list(found))

    # Technical Skills - Strict Whitelist approach
    doc = nlp(text)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in TECH_WHITELIST]
    matcher.add("TECH_ONLY", patterns)
    
    matches = matcher(doc)
    for _, start, end in matches:
        found.add(doc[start:end].text.title())
                
    return sorted(list(found))

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

def parse_resume(file_path: str) -> UserProfile:
    raw_text = extract_text(file_path)
    sections = get_sections(raw_text)
    full_text_cleaned = clean_text(raw_text)
    
    skills_raw = sections.get("SKILLS", raw_text)
    tech_skills = hybrid_tech_extraction(skills_raw, is_soft_skills=False)
    soft_skills = hybrid_tech_extraction(skills_raw, is_soft_skills=True)
    
    data = {
        "name": extract_name(full_text_cleaned),
        "email": extract_mail(full_text_cleaned),
        "phone": extract_phone(full_text_cleaned),
        "summary": sections.get("SUMMARY", "").strip() or None,
        "skills": tech_skills,
        "soft_skills": soft_skills,
        "education": extract_education(sections.get("EDUCATION", "")),
        "experience": extract_experience(sections.get("EXPERIENCE", "")),
        "projects": extract_projects(sections.get("PROJECTS", "")),
        "languages": [l.strip() for l in sections.get("LANGUAGES", "").replace(',', '\n').split('\n') if l.strip()],
        "certifications": [line.strip() for line in sections.get("CERTIFICATIONS", "").split('\n') if len(line.strip()) > 5],
        "interests": [i.strip() for i in sections.get("INTERESTS", "").replace(',', '\n').split('\n') if i.strip()]
    }
    
    address_match = re.search(r'\b\d{1,5}\s(?:[A-Z][a-z]+\s)+(?:Street|Road|Ave|Avenue|Lane|City|Bhopal|India)\b', full_text_cleaned)
    data["address"] = address_match.group(0) if address_match else None
    
    return UserProfile(**data)

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