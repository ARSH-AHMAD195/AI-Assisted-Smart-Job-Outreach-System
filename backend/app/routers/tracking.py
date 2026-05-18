"""
FastAPI router for email tracking endpoints.

Two tracking modes:
  1. Transactional (active) — Real-time tracking via webhook events stored locally
  2. Campaign (dormant) — Polling-based tracking via GMass campaign API, for future scale
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException

from app.schemas.tracking import (
    OpenRecord,
    ReplyRecord,
    CampaignSummary,
    CampaignTrackingReport,
    TrackingEvent,
    TrackingEventsResponse,
    TrackingSummaryResponse,
)
from app.services.gmass_tracking_client import GMassTrackingClient
from app.services.tracking_store import TrackingStore

router = APIRouter(prefix="/tracking", tags=["Tracking"])


# ─── Transactional Tracking (active — webhook-based) ───

@router.get(
    "/events",
    response_model=TrackingSummaryResponse,
    summary="Global tracking summary",
)
async def get_tracking_summary():
    """Returns aggregated tracking counts across all tracked emails."""
    store = TrackingStore()
    summary = store.get_summary()
    all_events = store.get_all_events()

    # Count unique emails
    unique_emails = set(e.get("email_address", "") for e in all_events if e.get("email_address"))

    return TrackingSummaryResponse(
        total_emails_tracked=len(unique_emails),
        opens=summary.get("opens", 0),
        replies=summary.get("replies", 0),
        bounces=summary.get("bounces", 0),
        clicks=summary.get("clicks", 0),
        sends=summary.get("sends", 0),
    )


@router.get(
    "/events/{email}",
    response_model=TrackingEventsResponse,
    summary="Tracking events for a recipient",
)
async def get_tracking_for_email(email: str):
    """Returns all tracking events for a specific recipient email."""
    store = TrackingStore()
    events = store.get_events_for_email(email)

    # Count by type
    opens = sum(1 for e in events if e.get("event_type", "").lower() == "opens")
    replies = sum(1 for e in events if e.get("event_type", "").lower() == "replies")
    bounces = sum(1 for e in events if e.get("event_type", "").lower() == "bounces")
    clicks = sum(1 for e in events if e.get("event_type", "").lower() == "clicks")

    return TrackingEventsResponse(
        email=email,
        total_events=len(events),
        opens=opens,
        replies=replies,
        bounces=bounces,
        clicks=clicks,
        events=[
            TrackingEvent(
                event_type=e.get("event_type", "unknown"),
                email_address=e.get("email_address", ""),
                tracking_id=e.get("tracking_id"),
                timestamp=e.get("timestamp"),
                received_at=e.get("received_at"),
            )
            for e in events
        ],
    )


@router.get(
    "/events/by-tracking-id/{tracking_id}",
    response_model=TrackingEventsResponse,
    summary="Tracking events by transactional email ID",
)
async def get_tracking_by_id(tracking_id: str):
    """Returns all tracking events for a specific transactional email ID."""
    store = TrackingStore()
    events = store.get_events_for_tracking_id(tracking_id)

    opens = sum(1 for e in events if e.get("event_type", "").lower() == "opens")
    replies = sum(1 for e in events if e.get("event_type", "").lower() == "replies")
    bounces = sum(1 for e in events if e.get("event_type", "").lower() == "bounces")
    clicks = sum(1 for e in events if e.get("event_type", "").lower() == "clicks")

    email = events[0].get("email_address", "") if events else None

    return TrackingEventsResponse(
        email=email,
        total_events=len(events),
        opens=opens,
        replies=replies,
        bounces=bounces,
        clicks=clicks,
        events=[
            TrackingEvent(
                event_type=e.get("event_type", "unknown"),
                email_address=e.get("email_address", ""),
                tracking_id=e.get("tracking_id"),
                timestamp=e.get("timestamp"),
                received_at=e.get("received_at"),
            )
            for e in events
        ],
    )


# ─── Campaign Tracking (dormant — for future mass email scale) ───

@router.get(
    "/campaign/{campaign_id}",
    response_model=CampaignTrackingReport,
    summary="Full campaign tracking report",
)
async def get_campaign_report(campaign_id: int):
    """
    Returns the full tracking report for a campaign, including
    opens, replies, and aggregated summary counts.
    """
    try:
        client = GMassTrackingClient()
        return await client.get_full_report(campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign tracking report: {str(e)}",
        )


@router.get(
    "/campaign/{campaign_id}/opens",
    response_model=List[OpenRecord],
    summary="Campaign open events",
)
async def get_campaign_opens(campaign_id: int):
    """Returns the list of open events for a campaign."""
    try:
        client = GMassTrackingClient()
        return await client.get_opens(campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign opens: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign opens: {str(e)}",
        )


@router.get(
    "/campaign/{campaign_id}/replies",
    response_model=List[ReplyRecord],
    summary="Campaign reply events",
)
async def get_campaign_replies(campaign_id: int):
    """Returns the list of reply events for a campaign."""
    try:
        client = GMassTrackingClient()
        return await client.get_replies(campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign replies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign replies: {str(e)}",
        )


@router.get(
    "/campaign/{campaign_id}/summary",
    response_model=CampaignSummary,
    summary="Campaign summary counts",
)
async def get_campaign_summary(campaign_id: int):
    """Returns aggregated tracking counts (opens, replies, bounces) for a campaign."""
    try:
        client = GMassTrackingClient()
        return await client.get_campaign_summary(campaign_id)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching campaign summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch campaign summary: {str(e)}",
        )
