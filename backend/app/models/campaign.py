"""
Campaign & OutreachQueueItem models — orchestrate controlled, multi-contact outreach.

Campaign:
    Groups outreach attempts under rate-limiting, company caps, and stagger settings.

OutreachQueueItem:
    Individual queued email with recipient-type-aware strategy, scheduling, and retry logic.
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.user_id"), index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, active, paused, completed
    target_role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Campaign-level delivery controls
    max_emails_per_hour = Column(Integer, default=10)
    max_contacts_per_company = Column(Integer, default=3)
    stagger_interval_minutes = Column(Integer, default=15)

    queue_items = relationship("OutreachQueueItem", back_populates="campaign", cascade="all, delete-orphan")
    user = relationship("User")


class OutreachQueueItem(Base):
    __tablename__ = "outreach_queue"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), index=True)
    contact_id = Column(Integer, ForeignKey("company_contacts.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("company_profiles.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True)

    recipient_email = Column(String, nullable=False)
    recipient_type = Column(String, nullable=True)   # "recruiter", "engineering", "founder", "hr", "careers"
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    outreach_style = Column(String, nullable=True)   # "concise_role_focused", "technical_project", "vision_oriented"

    status = Column(String, default="pending")       # pending, scheduled, sent, failed, skipped
    priority = Column(Integer, default=5)            # 1 = highest, 10 = lowest
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)

    transactional_id = Column(String, nullable=True, index=True)  # GMass tracking correlation

    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="queue_items")
    contact = relationship("CompanyContact")
