import re
from typing import List, Dict, Set, Tuple
from rapidfuzz import process, fuzz
from app.schemas.user import FinalUserProfile
from app.schemas.job import JobMatchResult
from app.utils.skills import hybrid_tech_extraction

# Header patterns for JD sectioning
JD_SECTION_MAP = {
    "MANDATORY": [
        "Requirements", "Must have", "Minimum Qualifications", "Responsibilities", 
        "Required Skills", "Technical Requirements", "What you will need", 
        "Key Qualifications", "Essential Skills"
    ],
    "PREFERRED": [
        "Preferred Qualifications", "Bonus", "Nice to have", "Plus", 
        "Desired Skills", "Good to have", "Other requirements"
    ]
}

def get_jd_sections(jd_text: str) -> Dict[str, str]:
    """Splits JD into Mandatory and Preferred sections using fuzzy header matching."""
    lines = [l.strip() for l in jd_text.split('\n')]
    sections = {"UNCLASSIFIED": ""}
    current_section = "UNCLASSIFIED"
    
    header_to_canonical = {}
    all_variations = []
    for canonical, variations in JD_SECTION_MAP.items():
        for v in variations:
            low_v = v.lower()
            all_variations.append(low_v)
            header_to_canonical[low_v] = canonical

    for line in lines:
        if not line:
            continue
            
        if len(line) < 40:
            match = process.extractOne(line.lower(), all_variations, scorer=fuzz.token_set_ratio)
            if match and match[1] > 80:
                current_section = header_to_canonical[match[0]]
                if current_section not in sections:
                    sections[current_section] = ""
                continue
        
        sections[current_section] += line + "\n"
        
    return sections

def calculate_match(user_profile: FinalUserProfile, jd_text: str) -> JobMatchResult:
    """Calculates weighted match score and identifies missing skills."""
    sections = get_jd_sections(jd_text)
    
    mandatory_text = sections.get("MANDATORY", "")
    preferred_text = sections.get("PREFERRED", "")
    # Add unclassified to mandatory as a safe default
    mandatory_text += sections.get("UNCLASSIFIED", "")
    
    mandatory_jd_skills = set(hybrid_tech_extraction(mandatory_text))
    preferred_jd_skills = set(hybrid_tech_extraction(preferred_text)) - mandatory_jd_skills
    
    user_skills = set([s.title() for s in user_profile.skills])
    
    matched_mandatory = user_skills.intersection(mandatory_jd_skills)
    matched_preferred = user_skills.intersection(preferred_jd_skills)
    
    missing_mandatory = mandatory_jd_skills - user_skills
    missing_preferred = preferred_jd_skills - user_skills
    
    # Scoring Logic
    # Mandatory = 2 pts, Preferred = 1 pt
    matched_score = (len(matched_mandatory) * 2) + (len(matched_preferred) * 1)
    total_jd_possible = (len(mandatory_jd_skills) * 2) + (len(preferred_jd_skills) * 1)
    
    score = (matched_score / total_jd_possible * 100) if total_jd_possible > 0 else 0
    
    # Labeling
    if score >= 80:
        label = "Excellent"
    elif score >= 50:
        label = "Good"
    else:
        label = "Poor"
        
    # Analysis summary
    analysis = f"Matched {len(matched_mandatory)}/{len(mandatory_jd_skills)} mandatory skills."
    if preferred_jd_skills:
        analysis += f" Matched {len(matched_preferred)}/{len(preferred_jd_skills)} preferred skills."
    
    return JobMatchResult(
        match_score=round(score, 2),
        match_label=label,
        matched_skills=sorted(list(matched_mandatory | matched_preferred)),
        missing_skills=sorted(list(missing_mandatory | missing_preferred)),
        analysis=analysis
    )
