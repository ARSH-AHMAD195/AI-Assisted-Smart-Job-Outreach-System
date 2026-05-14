from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.user import FinalUserProfile
from app.schemas.job import JobMatchResult
from app.schemas.job_intelligence import CompanyProfile

class EmailRequest(BaseModel):
    user_profile: FinalUserProfile
    job_match: JobMatchResult
    jd_text: str
    tone: str = "Professional"  # Professional, Enthusiastic, Concise, Creative
    recipient_name: Optional[str] = "Hiring Manager"
    company_intel: Optional[CompanyProfile] = None

class EmailResponse(BaseModel):
    subject_lines: List[str]
    body: str
    personalization_points: List[str]
    generated_at: str

class EmailSendRequest(BaseModel):
    sender_email: Optional[str] = None
    app_password: Optional[str] = None
    recipient_email: str
    subject: str
    body: str

