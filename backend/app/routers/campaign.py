"""
Campaign Router — REST endpoints for campaign management and outreach queue.

Endpoints:
    POST   /api/campaigns/                  → Create campaign
    GET    /api/campaigns/                  → List user's campaigns
    GET    /api/campaigns/{id}              → Campaign detail + queue status
    POST   /api/campaigns/{id}/populate     → Discover contacts + generate variants + enqueue
    POST   /api/campaigns/{id}/start        → Activate campaign
    POST   /api/campaigns/{id}/pause        → Pause campaign
    GET    /api/campaigns/{id}/queue        → View queue items
    DELETE /api/campaigns/{id}              → Delete campaign
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    QueuePopulateRequest,
    QueueItemResponse,
    QueueStatusResponse,
)
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new outreach campaign with delivery settings."""
    campaign = await CampaignService.create_campaign(db, current_user.user_id, payload)
    return await CampaignService.get_campaign_response(db, campaign)


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns for a user."""
    campaigns = await CampaignService.list_campaigns(db, current_user.user_id)
    responses = []
    for campaign in campaigns:
        resp = await CampaignService.get_campaign_response(db, campaign)
        responses.append(resp)
    return responses


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get campaign details with aggregated queue status."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this campaign")
    return await CampaignService.get_campaign_response(db, campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update campaign settings."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this campaign")
    campaign = await CampaignService.update_campaign(db, campaign_id, payload)
    return await CampaignService.get_campaign_response(db, campaign)


@router.post("/{campaign_id}/populate", response_model=QueueStatusResponse)
async def populate_campaign_queue(
    campaign_id: int,
    payload: QueuePopulateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Populate the campaign's outreach queue.
    For each job: discovers contacts → generates variant emails → enqueues with staggered scheduling.
    """
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to populate this campaign")

    try:
        result = await CampaignService.populate_queue(
            db,
            campaign_id,
            payload.job_ids,
            payload.user_profile_summary,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue population failed: {str(e)}")


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a campaign — starts queue processing via scheduler."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to start this campaign")
    campaign = await CampaignService.set_campaign_status(db, campaign_id, "active")
    return await CampaignService.get_campaign_response(db, campaign)


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a campaign — stops queue processing."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to pause this campaign")
    campaign = await CampaignService.set_campaign_status(db, campaign_id, "paused")
    return await CampaignService.get_campaign_response(db, campaign)


@router.get("/{campaign_id}/queue", response_model=list[QueueItemResponse])
async def get_queue_items(
    campaign_id: int,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """View outreach queue items for a campaign."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this campaign's queue")

    items = await CampaignService.get_queue_items(db, campaign_id, status)
    return [
        QueueItemResponse(
            id=item.id,
            campaign_id=item.campaign_id,
            recipient_email=item.recipient_email,
            recipient_type=item.recipient_type,
            outreach_style=item.outreach_style,
            subject=item.subject,
            body=item.body,
            status=item.status,
            priority=item.priority,
            scheduled_at=item.scheduled_at,
            sent_at=item.sent_at,
            retry_count=item.retry_count,
            error_message=item.error_message,
            transactional_id=item.transactional_id,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/{campaign_id}/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated queue status counts."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this campaign's status")
    return await CampaignService.get_queue_status(db, campaign_id)


@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign and all its queue items."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this campaign")
    success = await CampaignService.delete_campaign(db, campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"status": "deleted", "campaign_id": campaign_id}


@router.post("/{campaign_id}/queue/{queue_item_id}/send", response_model=QueueItemResponse)
async def send_queue_item_manually(
    campaign_id: int,
    queue_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger the send of a single queue item immediately."""
    campaign = await CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage this campaign")
        
    from app.models.campaign import OutreachQueueItem
    from sqlalchemy import select
    
    result = await db.execute(
        select(OutreachQueueItem).where(
            OutreachQueueItem.id == queue_item_id,
            OutreachQueueItem.campaign_id == campaign_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
        
    if item.status == "sent":
        raise HTTPException(status_code=400, detail="Item has already been sent")
        
    from app.services.outreach_queue_service import OutreachQueueService
    success = await OutreachQueueService._send_and_update(db, item)
    await db.commit()
    
    if not success:
        if item.status == "suppressed":
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "SUPPRESSED_FALLBACK",
                    "recipient": item.recipient_email,
                    "reason": item.error_message or "Recipient is on a bounce or unsubscribe list.",
                    "preserved_subject": item.subject,
                    "preserved_body": item.body,
                }
            )
        raise HTTPException(
            status_code=500,
            detail=item.error_message or "Failed to send queue item"
        )
        
    return QueueItemResponse(
        id=item.id,
        campaign_id=item.campaign_id,
        recipient_email=item.recipient_email,
        recipient_type=item.recipient_type,
        outreach_style=item.outreach_style,
        subject=item.subject,
        body=item.body,
        status=item.status,
        priority=item.priority,
        scheduled_at=item.scheduled_at,
        sent_at=item.sent_at,
        retry_count=item.retry_count,
        error_message=item.error_message,
        transactional_id=item.transactional_id,
        created_at=item.created_at,
    )

