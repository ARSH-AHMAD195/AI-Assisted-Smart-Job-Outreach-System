from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.outreach_analytics_service import OutreachAnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get high-level outreach analytics summary."""
    stats = await AnalyticsService.get_outreach_stats(db)
    return stats


@router.get("/campaigns/{campaign_id}")
async def get_campaign_analytics(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get campaign-level analytics: sent, opened, replied, bounced counts
    with engagement rates.
    """
    try:
        analytics = await OutreachAnalyticsService.get_campaign_analytics(db, campaign_id)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/variant-effectiveness")
async def get_variant_effectiveness(
    campaign_id: Optional[int] = Query(default=None, description="Filter by campaign ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze which outreach style gets the most engagement.
    Returns per-style metrics (sent, opened, replied, rates).
    """
    try:
        effectiveness = await OutreachAnalyticsService.get_variant_effectiveness(db, campaign_id)
        return effectiveness
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/company/{company_id}/engagement")
async def get_company_engagement(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the engagement score (0.0–1.0) for a company based on
    open/reply rates across all outreach to that company's contacts.
    """
    try:
        score = await OutreachAnalyticsService.get_company_engagement_score(db, company_id)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

