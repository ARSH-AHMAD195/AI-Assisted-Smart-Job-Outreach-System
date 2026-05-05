from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.user import FinalUserProfile
from app.schemas.job import JobMatchResult

class EmailRequest(BaseModel):
    user_profile: FinalUserProfile
    job_match: JobMatchResult
    jd_text: str
    tone: str = "Professional"  # Professional, Enthusiastic, Concise, Creative
    recipient_name: Optional[str] = "Hiring Manager"

class EmailResponse(BaseModel):
    subject_lines: List[str]
    body: str
    personalization_points: List[str]
    generated_at: str
