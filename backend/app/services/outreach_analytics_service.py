"""
Outreach Analytics Service — engagement scoring and variant effectiveness analysis.

Provides:
    - Campaign-level analytics (sent, opened, replied, bounced)
    - Variant effectiveness (which outreach style gets most engagement)
    - Company engagement scoring (0.0–1.0 based on interaction rates)

Cross-references outreach queue transactional IDs with tracking events
to build a feedback loop for strategy optimization.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, OutreachQueueItem
from app.models import TrackingEvent

logger = logging.getLogger(__name__)


class OutreachAnalyticsService:
    """Analytics and engagement intelligence for outreach campaigns."""

    @staticmethod
    async def get_campaign_analytics(db: AsyncSession, campaign_id: int) -> dict:
        """
        Aggregate campaign-level analytics by cross-referencing
        queue items with tracking events.

        Returns:
            Dict with sent, opened, replied, bounced counts + rates.
        """
        # Get all sent queue items for this campaign
        sent_result = await db.execute(
            select(OutreachQueueItem)
            .where(
                OutreachQueueItem.campaign_id == campaign_id,
                OutreachQueueItem.status == "sent",
            )
        )
        sent_items = list(sent_result.scalars().all())

        if not sent_items:
            return {
                "campaign_id": campaign_id,
                "total_sent": 0,
                "opened": 0,
                "replied": 0,
                "bounced": 0,
                "clicked": 0,
                "open_rate": 0.0,
                "reply_rate": 0.0,
                "bounce_rate": 0.0,
            }

        # Collect transactional IDs
        tracking_ids = [
            item.transactional_id for item in sent_items
            if item.transactional_id
        ]

        # Count events by type for these tracking IDs
        opened = 0
        replied = 0
        bounced = 0
        clicked = 0

        if tracking_ids:
            for event_type, counter_name in [
                ("OPEN", "opened"),
                ("REPLY", "replied"),
                ("BOUNCE", "bounced"),
                ("CLICK", "clicked"),
            ]:
                result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type == event_type,
                    )
                )
                count = result.scalar() or 0
                if counter_name == "opened":
                    opened = count
                elif counter_name == "replied":
                    replied = count
                elif counter_name == "bounced":
                    bounced = count
                elif counter_name == "clicked":
                    clicked = count

        total_sent = len(sent_items)

        return {
            "campaign_id": campaign_id,
            "total_sent": total_sent,
            "opened": opened,
            "replied": replied,
            "bounced": bounced,
            "clicked": clicked,
            "open_rate": round(opened / total_sent, 2) if total_sent > 0 else 0.0,
            "reply_rate": round(replied / total_sent, 2) if total_sent > 0 else 0.0,
            "bounce_rate": round(bounced / total_sent, 2) if total_sent > 0 else 0.0,
        }

    @staticmethod
    async def get_variant_effectiveness(
        db: AsyncSession,
        campaign_id: Optional[int] = None,
    ) -> dict:
        """
        Analyze which outreach_style gets the most engagement.

        Returns per-style metrics:
        {
            "technical_project": { "sent": 5, "opened": 3, "replied": 1, "open_rate": 0.6 },
            "concise_role_focused": { "sent": 8, "opened": 2, "replied": 0, "open_rate": 0.25 },
            ...
        }
        """
        # Query queue items, optionally filtered by campaign
        query = select(OutreachQueueItem).where(
            OutreachQueueItem.status == "sent",
            OutreachQueueItem.outreach_style.isnot(None),
        )
        if campaign_id:
            query = query.where(OutreachQueueItem.campaign_id == campaign_id)

        result = await db.execute(query)
        sent_items = list(result.scalars().all())

        # Group by outreach_style
        style_groups: Dict[str, list] = {}
        for item in sent_items:
            style = item.outreach_style or "unknown"
            if style not in style_groups:
                style_groups[style] = []
            style_groups[style].append(item)

        effectiveness = {}

        for style, items in style_groups.items():
            tracking_ids = [
                i.transactional_id for i in items if i.transactional_id
            ]
            sent_count = len(items)
            opened = 0
            replied = 0

            if tracking_ids:
                # Count opens
                open_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type == "OPEN",
                    )
                )
                opened = open_result.scalar() or 0

                # Count replies
                reply_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type == "REPLY",
                    )
                )
                replied = reply_result.scalar() or 0

            effectiveness[style] = {
                "sent": sent_count,
                "opened": opened,
                "replied": replied,
                "open_rate": round(opened / sent_count, 2) if sent_count > 0 else 0.0,
                "reply_rate": round(replied / sent_count, 2) if sent_count > 0 else 0.0,
            }

        return effectiveness

    @staticmethod
    async def get_company_engagement_score(
        db: AsyncSession,
        company_id: int,
    ) -> dict:
        """
        Calculate a 0.0–1.0 engagement score for a company based on
        open/reply rates across all outreach to that company's contacts.

        Scoring:
            - Each open = 0.3 weight
            - Each reply = 0.7 weight
            - Normalized against total sent
        """
        # Get all sent items for this company
        result = await db.execute(
            select(OutreachQueueItem).where(
                OutreachQueueItem.company_id == company_id,
                OutreachQueueItem.status == "sent",
            )
        )
        sent_items = list(result.scalars().all())

        if not sent_items:
            return {
                "company_id": company_id,
                "engagement_score": 0.0,
                "total_sent": 0,
                "opens": 0,
                "replies": 0,
                "detail": "No outreach sent to this company yet",
            }

        tracking_ids = [
            i.transactional_id for i in sent_items if i.transactional_id
        ]
        total_sent = len(sent_items)
        opens = 0
        replies = 0

        if tracking_ids:
            open_result = await db.execute(
                select(func.count(TrackingEvent.id))
                .where(
                    TrackingEvent.transactional_id.in_(tracking_ids),
                    TrackingEvent.event_type == "OPEN",
                )
            )
            opens = open_result.scalar() or 0

            reply_result = await db.execute(
                select(func.count(TrackingEvent.id))
                .where(
                    TrackingEvent.transactional_id.in_(tracking_ids),
                    TrackingEvent.event_type == "REPLY",
                )
            )
            replies = reply_result.scalar() or 0

        # Weighted engagement score
        open_weight = 0.3
        reply_weight = 0.7

        raw_score = (opens * open_weight + replies * reply_weight) / total_sent
        engagement_score = min(round(raw_score, 2), 1.0)

        return {
            "company_id": company_id,
            "engagement_score": engagement_score,
            "total_sent": total_sent,
            "opens": opens,
            "replies": replies,
        }
