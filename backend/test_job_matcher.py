from app.services.job_service import calculate_match
from app.schemas.user import FinalUserProfile, ResumeEntry

def test_matcher():
    # 1. Mock User Profile
    mock_profile = FinalUserProfile(
        name="Om Anand",
        email="om.d3v.21@gmail.com",
        phone="9142959347",
        address="Bhopal, India",
        experience=[],
        education=["B.Tech CSE"],
        certifications=[],
        languages=["English"],
        summary="Python Developer",
        skills=["Python", "Fastapi", "Docker", "Mysql"], # Matched skills
        soft_skills=["Communication"],
        interests=[],
        projects=[]
    )

    # 2. Mock JD String
    mock_jd = """
    We are looking for a Backend Engineer.
    
    Minimum Requirements:
    - Experience with Python and FastAPI.
    - Strong knowledge of MySQL.
    
    Preferred Qualifications:
    - Knowledge of Docker and AWS.
    - Understanding of Kubernetes.
    """

    print("Running Job Matcher Test...")
    result = calculate_match(mock_profile, mock_jd)
    
    print(f"Match Score: {result.match_score}%")
    print(f"Match Label: {result.match_label}")
    print(f"Matched Skills: {result.matched_skills}")
    print(f"Missing Skills: {result.missing_skills}")
    print(f"Analysis: {result.analysis}")

    # Expected:
    # Mandatory: Python, FastAPI, MySQL (All matched) -> 3*2 = 6 pts
    # Preferred: Docker, AWS, Kubernetes (Only Docker matched) -> 1*1 = 1 pt
    # Total JD possible: (3*2) + (3*1) = 9 pts
    # Expected Score: (7 / 9) * 100 = 77.78% (Label: Good)

    if result.match_score > 70:
        print("SUCCESS: Matcher correctly calculates weighted scores!")
    else:
        print("FAILURE: Score calculation mismatch.")

    if "Aws" in result.missing_skills and "Kubernetes" in result.missing_skills:
        print("SUCCESS: Missing skills correctly identified!")
    else:
        print(f"FAILURE: Missing skills incorrect: {result.missing_skills}")

if __name__ == "__main__":
    test_matcher()
