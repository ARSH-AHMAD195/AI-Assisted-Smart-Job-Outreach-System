"""
FastAPI router for receiving GMass webhook push notifications.

GMass sends POST requests to this endpoint when email events occur
(opens, replies, bounces, clicks, sends). Events are stored in the
tracking store for real-time dashboard updates.

Setup:
  1. Expose this endpoint via ngrok (for local dev)
  2. In GMass Dashboard → Settings → API → paste your webhook URL
  3. URL format: https://your-ngrok-url.ngrok.io/api/gmass-webhook
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Request
from app.services.tracking_store import TrackingStore

router = APIRouter(prefix="/api", tags=["Webhook"])


from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.models import TrackingEvent, OutreachEmail
from sqlalchemy import update, select

@router.post("/gmass-webhook")
async def gmass_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receive and store tracking events from GMass.
    """
    try:
        payload = await request.json()
    except Exception:
        form = await request.form()
        payload = dict(form)

    print(f"[Webhook] Received GMass event: {payload}")
    event_data = _normalize_event(payload)

    # 1. Store the event
    db_event = TrackingEvent(
        transactional_id=event_data["tracking_id"],
        event_type=event_data["event_type"],
        payload=event_data["raw_data"]
    )
    db.add(db_event)

    # 2. Update status of the corresponding outreach email
    if event_data["tracking_id"]:
        # Standardize event types for status update
        status_map = {
            "Opens": "OPENED",
            "Replies": "REPLIED",
            "Bounces": "BOUNCED",
            "Clicks": "CLICKED"
        }
        new_status = status_map.get(event_data["event_type"])
        if new_status:
            stmt = update(OutreachEmail).where(
                OutreachEmail.transactional_id == event_data["tracking_id"]
            ).values(status=new_status)
            await db.execute(stmt)

    await db.commit()
    return {"status": "ok", "message": "Event received"}


def _normalize_event(raw: dict) -> dict:
    """
    Normalize a GMass webhook payload into a consistent event format.

    GMass webhook payloads may include fields like:
    - emailAddress / email / EmailAddress
    - eventType / event / type
    - campaignId / CampaignId
    - timestamp / time / DateTime
    """
    # Try multiple possible field names for each value
    email = (
        raw.get("Email Address")
        or raw.get("emailAddress")
        or raw.get("EmailAddress")
        or raw.get("email")
        or raw.get("Email")
        or raw.get("to")
        or ""
    )

    event_type = (
        raw.get("eventType")
        or raw.get("EventType")
        or raw.get("event")
        or raw.get("type")
        or raw.get("platformSource")
    )

    # Distinguish event type based on bindings if explicit type is missing
    if not event_type:
        if "Bounce Message" in raw:
            event_type = "Bounces"
        elif "User Agent" in raw:
            event_type = "Opens"
        elif "Email Address" in raw:
            # If no User Agent and no Bounce Message, it's likely a Reply
            event_type = "Replies"
        else:
            event_type = "unknown"

    tracking_id = (
        raw.get("CorrelationID")
        or raw.get("correlationId")
        or raw.get("transactionalEmailId")
        or raw.get("TransactionalEmailId")
        or raw.get("messageId")
        or raw.get("MessageId")
        or ""
    )

    campaign_id = (
        raw.get("Campaign ID")
        or raw.get("campaignId")
        or raw.get("CampaignId")
        or raw.get("campaign_id")
    )

    timestamp = (
        raw.get("Time Stamp")
        or raw.get("timestamp")
        or raw.get("Timestamp")
        or raw.get("DateTime")
        or raw.get("dateTime")
        or raw.get("time")
    )

    return {
        "event_type": event_type,
        "email_address": email,
        "tracking_id": str(tracking_id) if tracking_id else "",
        "campaign_id": campaign_id,
        "timestamp": timestamp,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "raw_data": raw,
    }
