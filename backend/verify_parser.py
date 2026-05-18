from app.services.resume__service import parse_resume, clean_text, extract_name, get_sections
from app.schemas.user import UserProfile
import re

# Mock the extracted text from the user's resume
resume_text = """
Bhopal, M.P
9142959347 O m A n a n d om.d3v.21@gmail.com
https://portfolio-seven-
chi-44.vercel.app/
Education
Gandhinagar, Bhopal,M.P Sagar Institute of Science &
Technology
Sept 2024 | Sept 2027
• B.Tech in Computer Science. GPA: 7
Skills
• Programming Languages: Java, C++, C, Python
• Web Development: HTML, CSS, JavaScript
• Tools & Platforms: Git & GitHub, VS Code, IntelliJ IDEA, Linux
• Soft Skills: Team Collaboration, Problem Solving, Presentation Skills, Time Management, Self-
Learning
• CS Fundamentals: D.S.A, OOP
Projects
• Java ERP System | Java, MySQL Designed and developed an Employee Dashboard using Java Swing and FlatLaf.
- Implemented attendance tracking with date-picker and toggle buttons. - Built authentication and
user profile mapping logic. Java, MySQL
• Selection Sort Visualizer | C++, SFML (https://github.com/Om-anand-0/civic-storm) Created a real-time
visualizer for the Selection Sort algorithm using SFML to provide visual feedback on the sorting
process. Gained experience with recursions and sorting methods C++, SMFL
• Real-Time Face Recognition System | Python, OpenCV Built a real-time facial recognition app using webcam
input. Developed a modular system for loading known faces, encoding, and live identification with
error handling. Designed a visual interface with color-coded bounding boxes and name tags. Applied
face detection, landmark identification, and embedding comparison techniques, ensuring scalability
for adding new faces. Python, NumPy, face_recognition, OpenCV
"""

def test_final_parser_precision():
    print("Testing Final Parser Precision Refactor Accuracy...")
    cleaned = clean_text(resume_text)
    
    sections = get_sections(resume_text)
    print(f"Detected Sections: {list(sections.keys())}")
    
    # Check name extraction
    name = extract_name(cleaned)
    print(f"Extracted Name: {name}")
    
    # Core logic extraction
    from app.services.resume__service import (
        extract_mail, extract_phone, extract_education, 
        extract_projects, hybrid_tech_extraction, TECH_WHITELIST
    )
    
    email = extract_mail(cleaned)
    phone = extract_phone(cleaned)
    education = extract_education(sections.get("EDUCATION"))
    
    # Technical skills must be strict whitelist
    skills_raw = sections.get("SKILLS", "")
    tech_skills = hybrid_tech_extraction(skills_raw, is_soft_skills=False)
    soft_skills = hybrid_tech_extraction(skills_raw, is_soft_skills=True)
    
    projects = extract_projects(sections.get("PROJECTS"))
    
    print(f"Extracted Email: {email}")
    print(f"Extracted Phone: {phone}")
    print(f"Extracted Education: {education}")
    print(f"Extracted Technical Skills (Strict): {tech_skills}")
    print(f"Extracted Soft Skills: {soft_skills}")
    
    print(f"Extracted Projects: {len(projects)} found")
    for idx, p in enumerate(projects):
        print(f"  Project {idx+1}: {p.title}")
        print(f"    Tech Stack: {p.tech_stack}")
        print(f"    Description Lines: {len(p.description)}")
        
    # Assertions
    if name == "Om Anand":
         print("SUCCESS: Name identified correctly!")
    else:
         print(f"FAILURE: Name identified as {name}. Expecting 'Om Anand'.")

    # Strict Tech Skill Check
    if all(s.lower() in TECH_WHITELIST for s in tech_skills):
        print("SUCCESS: Skills list is 100% clean (only whitelisted tech)!")

    # Project Grouping Check
    if len(projects) == 3:
        print("SUCCESS: Project Grouping (State-Machine) is perfectly segmented!")
    else:
        print(f"FAILURE: Project count is {len(projects)}. Expecting 3.")

    if "Problem Solving" in soft_skills and "Problem Solving" not in tech_skills:
        print("SUCCESS: Soft Skills correctly mapped separately!")

if __name__ == "__main__":
    test_final_parser_precision()
