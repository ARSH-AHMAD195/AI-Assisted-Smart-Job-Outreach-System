from sqlalchemy.future import select
from sqlalchemy import func
from app.models import OutreachEmail, TrackingEvent
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

class AnalyticsService:
    @staticmethod
    async def get_outreach_stats(db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregate outreach statistics.
        """
        # Total sent
        sent_query = select(func.count(OutreachEmail.id))
        sent_result = await db.execute(sent_query)
        total_sent = sent_result.scalar()
        
        # Total opened
        opened_query = select(func.count(TrackingEvent.id)).where(TrackingEvent.event_type == "OPEN")
        opened_result = await db.execute(opened_query)
        total_opened = opened_result.scalar()
        
        # Reply rate
        replied_query = select(func.count(TrackingEvent.id)).where(TrackingEvent.event_type == "REPLY")
        replied_result = await db.execute(replied_query)
        total_replied = replied_result.scalar()
        
        # Best strategy
        strategy_query = select(
            OutreachEmail.strategy, 
            func.count(OutreachEmail.id).label("count")
        ).group_by(OutreachEmail.strategy).order_by(func.count(OutreachEmail.id).desc()).limit(1)
        strategy_result = await db.execute(strategy_query)
        best_strategy = strategy_result.first()
        
        return {
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_replied": total_replied,
            "open_rate": (total_opened / total_sent * 100) if total_sent > 0 else 0,
            "reply_rate": (total_replied / total_sent * 100) if total_sent > 0 else 0,
            "best_performing_strategy": best_strategy[0] if best_strategy else "N/A"
        }
