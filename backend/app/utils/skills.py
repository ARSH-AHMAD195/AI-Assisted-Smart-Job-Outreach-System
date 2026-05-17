import re
import spacy
from spacy.matcher import PhraseMatcher
from typing import List, Set, Dict

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")

# Categorized Skills Database (The master whitelist)
SKILLS_DB = {
    "Languages": ["Python", "Java", "C++", "C", "JavaScript", "TypeScript", "SQL", "HTML", "CSS", "Go", "Rust", "PHP", "Ruby", "Swift", "Kotlin"],
    "Frontend": ["React", "Angular", "Vue", "Next.js", "Tailwind CSS", "Bootstrap", "Svelte", "Redux", "Vite", "jQuery", "UI/UX"],
    "Backend": ["FastAPI", "Django", "Flask", "Node.js", "Express.js", "Spring Boot", "Laravel", "Postman", "GraphQL", "REST API"],
    "DevOps/Cloud": ["Docker", "Kubernetes", "AWS", "Azure", "GCP", "Git", "GitHub", "Jenkins", "Terraform", "Linux", "CI/CD", "Prometheus"],
    "Data/AI": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "NumPy", "Pandas", "Scikit-learn", "OpenCV", "Face Recognition", "R Language", "Spark"],
    "Databases": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "SQLite", "Oracle", "Cassandra", "Elasticsearch", "Prisma"]
}

TECH_WHITELIST = {skill.lower() for cat in SKILLS_DB.values() for skill in cat}

SOFT_SKILL_KEYWORDS = ["Communication", "Teamwork", "Problem Solving", "Leadership", "Presentation", "Self-Learning", "Time Management", "Collaboration", "Decision Making", "Adaptability"]

def hybrid_tech_extraction(text: str, is_soft_skills: bool = False) -> List[str]:
    """Extracts tech stack strictly against the TECH_WHITELIST."""
    found = set()
    
    if is_soft_skills:
        for sk in SOFT_SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(sk) + r'\b', text, re.IGNORECASE):
                found.add(sk)
        return sorted(list(found))

    doc = nlp(text)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in TECH_WHITELIST]
    matcher.add("TECH_ONLY", patterns)
    
    matches = matcher(doc)
    for _, start, end in matches:
        found.add(doc[start:end].text.title())
                
    return sorted(list(found))
