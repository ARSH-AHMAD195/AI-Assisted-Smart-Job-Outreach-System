from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class EmailGenerateRequest(BaseModel):
    company_id: int
    tone: Optional[str] = "professional"
    job_role: Optional[str] = None


class ApproveEmailRequest(BaseModel):
    approved: bool = True


class EmailResponse(BaseModel):
    id: UUID
    subject: str
    body: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True