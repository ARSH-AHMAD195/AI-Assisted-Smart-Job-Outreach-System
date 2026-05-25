"""
Adaptive Optimizer Service — closes the feedback loop.

Responsible for:
    1. Behavioral confidence updates — opens/replies/bounces shape contact scores
    2. Strategy performance aggregation — per-industry, per-contact-type breakdowns
    3. Strategy insights — enriches strategy recommendations with "best_for" context
    4. Daily optimization job — periodic aggregation and score updates

This is the engine that turns tracking data into strategic intelligence.

Separates three confidence dimensions:
    - contact_confidence: How responsive is this specific contact?
    - strategy_confidence: How well does this strategy perform in context?
    - company_engagement_score: How engaged is this company overall?
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, OutreachQueueItem
from app.models.contact import CompanyContact
from app.models.outreach_event import OutreachEvent
from app.models import TrackingEvent, CompanyProfile

logger = logging.getLogger(__name__)


# Behavioral confidence deltas per tracking event
EVENT_CONFIDENCE_DELTAS = {
    "OPEN":   +0.05,
    "Opens":  +0.05,
    "REPLY":  +0.15,
    "Replies": +0.15,
    "BOUNCE": -0.20,
    "Bounces": -0.20,
    "CLICK":  +0.03,
    "Clicks": +0.03,
}


class AdaptiveOptimizerService:
    """
    Feedback-driven optimization engine.
    Transforms tracking signals into strategic intelligence.
    """

    @classmethod
    async def run_daily_optimization(cls, db: AsyncSession):
        """
        Main daily optimization job. Called by the scheduler.

        Steps:
            1. Update contact behavioral confidence from recent events
            2. Aggregate strategy performance with context
            3. Decay stale confidence scores (no activity = slight decay)
            4. Emit optimization event
        """
        logger.info("Starting daily optimization run...")

        # 1. Update behavioral confidence
        updated_contacts = await cls._update_behavioral_confidence(db)

        # 2. Aggregate strategy insights
        strategy_insights = await cls.get_strategy_insights(db)

        # 3. Decay stale contacts (no activity in 14 days)
        decayed = await cls._decay_stale_confidence(db, days=14, decay_amount=0.03)

        # 4. Emit optimization event
        event = OutreachEvent(
            event_type="optimization_completed",
            entity_type="system",
            entity_id="daily_optimizer",
            payload={
                "contacts_updated": updated_contacts,
                "contacts_decayed": decayed,
                "strategies_analyzed": len(strategy_insights),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
        db.add(event)
        await db.commit()

        logger.info(
            f"Optimization complete: {updated_contacts} contacts updated, "
            f"{decayed} decayed, {len(strategy_insights)} strategies analyzed"
        )

    @classmethod
    async def _update_behavioral_confidence(cls, db: AsyncSession) -> int:
        """
        Update contact confidence scores based on tracking events
        from the last 24 hours.
        """
        yesterday = datetime.utcnow() - timedelta(hours=24)

        # Get recent tracking events
        result = await db.execute(
            select(TrackingEvent)
            .where(TrackingEvent.timestamp >= yesterday)
        )
        recent_events = list(result.scalars().all())

        if not recent_events:
            return 0

        updated_count = 0

        for event in recent_events:
            if not event.transactional_id:
                continue

            delta = EVENT_CONFIDENCE_DELTAS.get(event.event_type, 0.0)
            if delta == 0.0:
                continue

            # Find the queue item → contact
            qi_result = await db.execute(
                select(OutreachQueueItem).where(
                    OutreachQueueItem.transactional_id == event.transactional_id
                )
            )
            queue_item = qi_result.scalars().first()
            if not queue_item or not queue_item.contact_id:
                continue

            # Update contact confidence
            contact_result = await db.execute(
                select(CompanyContact).where(
                    CompanyContact.id == queue_item.contact_id
                )
            )
            contact = contact_result.scalars().first()
            if contact:
                old_score = contact.confidence_score
                contact.confidence_score = max(0.0, min(1.0, old_score + delta))
                updated_count += 1

        if updated_count > 0:
            await db.commit()

        return updated_count

    @classmethod
    async def _decay_stale_confidence(
        cls, db: AsyncSession, days: int = 14, decay_amount: float = 0.03,
    ) -> int:
        """
        Slightly decay confidence for contacts with no activity in N days.
        Prevents stale high-confidence contacts from dominating recommendations.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        # Contacts that were last contacted before the cutoff
        result = await db.execute(
            select(CompanyContact).where(
                CompanyContact.last_contacted_at < cutoff,
                CompanyContact.confidence_score > 0.1,  # Don't decay below floor
            )
        )
        stale_contacts = list(result.scalars().all())

        count = 0
        for contact in stale_contacts:
            contact.confidence_score = max(0.1, contact.confidence_score - decay_amount)
            count += 1

        if count > 0:
            await db.commit()

        return count

    @classmethod
    async def get_strategy_insights(cls, db: AsyncSession) -> Dict[str, Dict]:
        """
        Aggregate strategy performance with contextual breakdowns.

        Returns:
        {
            "technical_project": {
                "total_sent": 47,
                "open_rate": 0.34,
                "reply_rate": 0.12,
                "best_for": ["AI startups", "engineering contacts"],
                "breakdown": {
                    "by_contact_type": { "engineering": {"open_rate": 0.45}, ... },
                    "by_company_type": { ... }
                }
            }
        }
        """
        # Get all sent queue items with styles
        result = await db.execute(
            select(OutreachQueueItem).where(
                OutreachQueueItem.status == "sent",
                OutreachQueueItem.outreach_style.isnot(None),
            )
        )
        sent_items = list(result.scalars().all())

        if not sent_items:
            return {}

        # Group by style
        style_groups: Dict[str, List] = defaultdict(list)
        for item in sent_items:
            style_groups[item.outreach_style or "unknown"].append(item)

        insights = {}

        for style, items in style_groups.items():
            tracking_ids = [i.transactional_id for i in items if i.transactional_id]
            total_sent = len(items)

            # Count events
            opened = 0
            replied = 0
            if tracking_ids:
                open_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type.in_(["OPEN", "Opens"]),
                    )
                )
                opened = open_result.scalar() or 0

                reply_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type.in_(["REPLY", "Replies"]),
                    )
                )
                replied = reply_result.scalar() or 0

            open_rate = round(opened / total_sent, 2) if total_sent else 0.0
            reply_rate = round(replied / total_sent, 2) if total_sent else 0.0

            # Breakdown by contact type
            by_contact_type = defaultdict(lambda: {"sent": 0, "tracking_ids": []})
            for item in items:
                ct = item.recipient_type or "unknown"
                by_contact_type[ct]["sent"] += 1
                if item.transactional_id:
                    by_contact_type[ct]["tracking_ids"].append(item.transactional_id)

            contact_breakdown = {}
            for ct, data in by_contact_type.items():
                ct_opened = 0
                ct_replied = 0
                if data["tracking_ids"]:
                    ct_open_result = await db.execute(
                        select(func.count(TrackingEvent.id))
                        .where(
                            TrackingEvent.transactional_id.in_(data["tracking_ids"]),
                            TrackingEvent.event_type.in_(["OPEN", "Opens"]),
                        )
                    )
                    ct_opened = ct_open_result.scalar() or 0

                    ct_reply_result = await db.execute(
                        select(func.count(TrackingEvent.id))
                        .where(
                            TrackingEvent.transactional_id.in_(data["tracking_ids"]),
                            TrackingEvent.event_type.in_(["REPLY", "Replies"]),
                        )
                    )
                    ct_replied = ct_reply_result.scalar() or 0

                contact_breakdown[ct] = {
                    "sent": data["sent"],
                    "open_rate": round(ct_opened / data["sent"], 2) if data["sent"] else 0.0,
                    "reply_rate": round(ct_replied / data["sent"], 2) if data["sent"] else 0.0,
                }

            # Determine "best_for" — which contexts this strategy excels in
            best_for = []
            for ct, metrics in contact_breakdown.items():
                if metrics["reply_rate"] > 0.1:
                    best_for.append(f"{ct} contacts")
                elif metrics["open_rate"] > 0.3:
                    best_for.append(f"{ct} contacts (opens)")

            insights[style] = {
                "total_sent": total_sent,
                "opened": opened,
                "replied": replied,
                "open_rate": open_rate,
                "reply_rate": reply_rate,
                "best_for": best_for,
                "breakdown": {
                    "by_contact_type": contact_breakdown,
                },
            }

        return insights

    @classmethod
    async def get_optimization_report(cls, db: AsyncSession) -> Dict:
        """
        Get the current optimization state — behavioral scores + strategy performance.
        Used by the intelligence API.
        """
        # Strategy insights
        strategy_insights = await cls.get_strategy_insights(db)

        # Recent optimization events
        result = await db.execute(
            select(OutreachEvent)
            .where(OutreachEvent.event_type == "optimization_completed")
            .order_by(OutreachEvent.created_at.desc())
            .limit(5)
        )
        recent_optimizations = [
            {
                "timestamp": str(e.created_at),
                "payload": e.payload,
            }
            for e in result.scalars().all()
        ]

        # Reply classification summary
        reply_result = await db.execute(
            select(OutreachEvent)
            .where(OutreachEvent.event_type == "reply_classified")
        )
        reply_events = list(reply_result.scalars().all())

        intent_counts = defaultdict(int)
        for e in reply_events:
            if e.payload and "intent" in e.payload:
                intent_counts[e.payload["intent"]] += 1

        return {
            "strategy_insights": strategy_insights,
            "reply_classifications": dict(intent_counts),
            "total_replies_classified": len(reply_events),
            "recent_optimizations": recent_optimizations,
            "last_optimization": recent_optimizations[0]["timestamp"] if recent_optimizations else None,
        }
