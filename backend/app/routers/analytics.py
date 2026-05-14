from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get high-level outreach analytics summary."""
    stats = await AnalyticsService.get_outreach_stats(db)
    return stats
