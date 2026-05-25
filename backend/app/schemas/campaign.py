"""
Pydantic schemas for Campaign management and Outreach Queue.

Defines request/response models for creating campaigns,
populating outreach queues, and tracking queue item status.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- Campaign CRUD ---

class CampaignCreate(BaseModel):
    """Request to create a new outreach campaign."""
    name: str
    target_role: Optional[str] = None
    max_emails_per_hour: int = Field(default=10, ge=1, le=50)
    max_contacts_per_company: int = Field(default=3, ge=1, le=10)
    stagger_interval_minutes: int = Field(default=15, ge=5, le=120)


class CampaignUpdate(BaseModel):
    """Request to update campaign settings."""
    name: Optional[str] = None
    max_emails_per_hour: Optional[int] = Field(default=None, ge=1, le=50)
    max_contacts_per_company: Optional[int] = Field(default=None, ge=1, le=10)
    stagger_interval_minutes: Optional[int] = Field(default=None, ge=5, le=120)


class CampaignResponse(BaseModel):
    """Response for a campaign with aggregated status."""
    id: int
    name: str
    status: str
    target_role: Optional[str] = None
    max_emails_per_hour: int
    max_contacts_per_company: int
    stagger_interval_minutes: int
    queue_size: int = 0
    sent_count: int = 0
    failed_count: int = 0
    pending_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Queue Population ---

class QueuePopulateRequest(BaseModel):
    """Request to populate a campaign's outreach queue."""
    job_ids: List[int] = Field(
        description="Job listing IDs to discover contacts for and generate outreach variants"
    )
    user_profile_summary: Optional[str] = Field(
        default=None,
        description="Brief user profile summary for email generation context"
    )


# --- Queue Item ---

class QueueItemResponse(BaseModel):
    """Response for a single outreach queue item."""
    id: int
    campaign_id: int
    recipient_email: str
    recipient_type: Optional[str] = None
    outreach_style: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    status: str
    priority: int
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None
    transactional_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QueueStatusResponse(BaseModel):
    """Aggregated queue status for a campaign."""
    campaign_id: int
    total: int = 0
    pending: int = 0
    scheduled: int = 0
    sent: int = 0
    failed: int = 0
    skipped: int = 0
