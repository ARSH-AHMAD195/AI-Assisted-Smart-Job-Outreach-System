"""
CompanyContact model — stores discovered public contact channels for companies.

Each company may have multiple contacts (careers@, hr@, recruiting@, etc.)
with confidence scores based on source reliability and email pattern matching.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class CompanyContact(Base):
    __tablename__ = "company_contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), index=True)
    email = Column(String, nullable=False, index=True)
    contact_type = Column(String, nullable=False)  # "careers", "recruiting", "hr", "engineering", "founder"
    source = Column(String, nullable=True)          # "careers_page", "about_page", "job_listing", "contact_page"
    confidence_score = Column(Float, default=0.5)
    is_verified = Column(Boolean, default=False)
    last_contacted_at = Column(DateTime, nullable=True)
    contact_count = Column(Integer, default=0)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("CompanyProfile", back_populates="contacts")
