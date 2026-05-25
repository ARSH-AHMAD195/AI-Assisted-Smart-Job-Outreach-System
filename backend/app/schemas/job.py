from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.user import FinalUserProfile

class JobMatchRequest(BaseModel):
    user_profile: FinalUserProfile
    jd_text: str

class JobMatchResult(BaseModel):
    match_score: float = Field(..., ge=0, le=100)
    match_label: str  # Excellent / Good / Poor
    matched_skills: List[str]
    missing_skills: List[str]
    analysis: str

class JobListing(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    description: str
    job_url: Optional[str] = None
    emails: List[str] = []
