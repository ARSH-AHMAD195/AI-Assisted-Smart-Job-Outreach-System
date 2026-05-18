from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from app.schemas.user import FinalUserProfile
from app.schemas.job import JobMatchResult
from app.schemas.job_intelligence import CompanyProfile


# --- Database Email Schemas (from HEAD) ---

class EmailGenerateRequest(BaseModel):
    company_id: int
    tone: Optional[str] = "professional"
    job_role: Optional[str] = None


class ApproveEmailRequest(BaseModel):
    approved: bool = True


class DBEmailResponse(BaseModel):
    id: UUID
    subject: str
    body: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- AI/Outreach Email Schemas (from main) ---

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
