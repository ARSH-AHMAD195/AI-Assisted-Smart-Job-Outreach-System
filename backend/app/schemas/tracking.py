"""
Pydantic response models for GMass email tracking endpoints.

Defines typed schemas for:
- Campaign tracking (opens, replies, summary, full report) — dormant, for future scale
- Transactional tracking (webhook events, event queries)
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ─── Campaign Tracking (dormant — for future mass email scale) ───

class OpenRecord(BaseModel):
    """A single email open event."""
    email: str
    open_count: int
    last_opened_at: Optional[str] = None


class ReplyRecord(BaseModel):
    """A single email reply event."""
    email: str
    replied_at: Optional[str] = None


class CampaignSummary(BaseModel):
    """Aggregated campaign tracking counts."""
    open_count: int = 0
    reply_count: int = 0
    bounce_count: int = 0


class CampaignTrackingReport(BaseModel):
    """Full tracking report for a GMass campaign."""
    campaign_id: int
    fetched_at: str
    summary: CampaignSummary
    opens: List[OpenRecord] = []
    replies: List[ReplyRecord] = []


# ─── Transactional Tracking (active — webhook-based) ───

class WebhookEvent(BaseModel):
    """Schema for an incoming GMass webhook event payload."""
    event_type: str  # Opens, Replies, Bounces, Clicks, Sends
    email_address: str
    tracking_id: Optional[str] = None
    campaign_id: Optional[int] = None
    timestamp: Optional[str] = None
    received_at: Optional[str] = None
    raw_data: Optional[dict] = None


class TrackingEvent(BaseModel):
    """A stored tracking event from the webhook store."""
    event_type: str
    email_address: str
    tracking_id: Optional[str] = None
    timestamp: Optional[str] = None
    received_at: Optional[str] = None


class TrackingEventsResponse(BaseModel):
    """Response for tracking events query."""
    email: Optional[str] = None
    total_events: int = 0
    opens: int = 0
    replies: int = 0
    bounces: int = 0
    clicks: int = 0
    events: List[TrackingEvent] = []


class TrackingSummaryResponse(BaseModel):
    """Global tracking summary across all emails."""
    total_emails_tracked: int = 0
    opens: int = 0
    replies: int = 0
    bounces: int = 0
    clicks: int = 0
    sends: int = 0


class TransactionalSendResponse(BaseModel):
    """Response from sending a transactional email."""
    status: str
    message: str
    sender: str
    tracking_id: Optional[str] = None
    tracking_enabled: bool = True
