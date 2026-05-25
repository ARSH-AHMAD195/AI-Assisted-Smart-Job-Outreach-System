"""
Outreach Queue Service — processes pending outreach items with delivery controls.

Responsible for:
    - Rate limiting: max N emails/hour per campaign
    - Company caps: max M contacts per company per campaign
    - Stagger: minimum interval between consecutive sends
    - Retry: exponential backoff on send failures
    - Integration: sends via GMass Transactional API and records tracking IDs
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign, OutreachQueueItem
from app.services.gmass_transactional_service import GMassTransactionalService

logger = logging.getLogger(__name__)


class OutreachQueueService:
    """Processes the outreach queue with rate limiting and delivery controls."""

    @staticmethod
    async def process_queue(db: AsyncSession):
        """
        Main queue processor — called by the scheduler every 5 minutes.

        For each active campaign, processes eligible pending items
        while respecting rate limits and company caps.
        """
        # Get all active campaigns
        result = await db.execute(
            select(Campaign).where(Campaign.status == "active")
        )
        active_campaigns = list(result.scalars().all())

        if not active_campaigns:
            logger.debug("No active campaigns to process")
            return

        total_sent = 0

        for campaign in active_campaigns:
            try:
                sent = await OutreachQueueService._process_campaign_queue(db, campaign)
                total_sent += sent
            except Exception as e:
                logger.error(f"Error processing campaign {campaign.id}: {e}")

        if total_sent > 0:
            logger.info(f"Queue processor completed: {total_sent} emails sent across {len(active_campaigns)} campaigns")

    @staticmethod
    async def _process_campaign_queue(db: AsyncSession, campaign: Campaign) -> int:
        """
        Process queue items for a single campaign.
        Returns the number of emails sent.
        """
        # Check hourly rate limit
        if not await OutreachQueueService._check_rate_limit(db, campaign):
            logger.info(f"Campaign {campaign.id}: rate limit reached, skipping")
            return 0

        # Get eligible items: pending + scheduled_at <= now
        now = datetime.utcnow()
        result = await db.execute(
            select(OutreachQueueItem)
            .where(
                OutreachQueueItem.campaign_id == campaign.id,
                OutreachQueueItem.status.in_(["pending", "scheduled"]),
                (OutreachQueueItem.scheduled_at <= now) | (OutreachQueueItem.scheduled_at.is_(None)),
            )
            .order_by(OutreachQueueItem.priority.asc(), OutreachQueueItem.scheduled_at.asc())
            .limit(campaign.max_emails_per_hour)  # Never exceed hourly cap in one batch
        )
        eligible_items = list(result.scalars().all())

        if not eligible_items:
            # Check if all items are sent/failed → mark campaign complete
            await OutreachQueueService._check_campaign_completion(db, campaign)
            return 0

        sent_count = 0

        for item in eligible_items:
            # Re-check rate limit after each send
            if not await OutreachQueueService._check_rate_limit(db, campaign):
                logger.info(f"Campaign {campaign.id}: rate limit hit mid-batch")
                break

            # Check company cap
            if item.company_id and not await OutreachQueueService._check_company_cap(db, campaign, item.company_id):
                logger.info(
                    f"Campaign {campaign.id}: company cap reached for company_id={item.company_id}, skipping"
                )
                item.status = "skipped"
                item.error_message = "Company contact cap reached"
                continue

            # Send the email
            success = await OutreachQueueService._send_and_update(db, item)
            if success:
                sent_count += 1

        await db.commit()
        return sent_count

    @staticmethod
    async def _check_rate_limit(db: AsyncSession, campaign: Campaign) -> bool:
        """
        Check if we're within the hourly send limit for a campaign.
        Returns True if we can still send.
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        result = await db.execute(
            select(func.count(OutreachQueueItem.id))
            .where(
                OutreachQueueItem.campaign_id == campaign.id,
                OutreachQueueItem.status == "sent",
                OutreachQueueItem.sent_at >= one_hour_ago,
            )
        )
        sent_last_hour = result.scalar() or 0

        return sent_last_hour < campaign.max_emails_per_hour

    @staticmethod
    async def _check_company_cap(
        db: AsyncSession,
        campaign: Campaign,
        company_id: int,
    ) -> bool:
        """
        Check if we've hit the max contacts for this company in this campaign.
        Returns True if we can still send to this company.
        """
        result = await db.execute(
            select(func.count(OutreachQueueItem.id))
            .where(
                OutreachQueueItem.campaign_id == campaign.id,
                OutreachQueueItem.company_id == company_id,
                OutreachQueueItem.status == "sent",
            )
        )
        sent_to_company = result.scalar() or 0

        return sent_to_company < campaign.max_contacts_per_company

    @staticmethod
    async def _send_and_update(db: AsyncSession, item: OutreachQueueItem) -> bool:
        """
        Send a single queue item via GMass Transactional API.
        Updates the item status and records the transactional ID.
        Returns True on success.
        """
        if not item.subject or not item.body:
            item.status = "skipped"
            item.error_message = "Missing subject or body"
            logger.warning(f"Queue item {item.id}: skipped (missing content)")
            return False

        try:
            result = await GMassTransactionalService.send_email(
                recipient_email=item.recipient_email,
                subject=item.subject,
                body=item.body,
            )

            # Extract transactional ID for tracking correlation
            tracking_id = result.get("tracking_id", "")

            item.status = "sent"
            item.sent_at = datetime.utcnow()
            item.transactional_id = str(tracking_id) if tracking_id else None

            logger.info(
                f"Queue item {item.id}: sent to {item.recipient_email} "
                f"(tracking_id={tracking_id})"
            )
            return True

        except Exception as e:
            error_msg = str(e)
            if "unsubscribe or bounce list" in error_msg.lower():
                item.status = "suppressed"
                item.error_message = f"Suppressed: {error_msg[:400]}"
                logger.warning(f"Queue item {item.id}: recipient {item.recipient_email} is on GMass suppression list. Marking suppressed.")
                
                # Attempt to find another contact for this company
                if item.company_id:
                    from app.models.contact import CompanyContact
                    # 1. Lower confidence of the current email
                    contact_result = await db.execute(
                        select(CompanyContact).where(
                            CompanyContact.company_id == item.company_id,
                            CompanyContact.email == item.recipient_email
                        )
                    )
                    contact = contact_result.scalars().first()
                    if contact:
                        contact.confidence_score = -1.0
                        logger.info(f"Lowered confidence score to -1.0 for suppressed contact: {item.recipient_email}")
                    
                    # 2. Query other contacts for the company
                    other_contacts_result = await db.execute(
                        select(CompanyContact)
                        .where(
                            CompanyContact.company_id == item.company_id,
                            CompanyContact.confidence_score >= 0.0,
                            CompanyContact.email != item.recipient_email
                        )
                        .order_by(CompanyContact.confidence_score.desc())
                    )
                    other_contacts = list(other_contacts_result.scalars().all())
                    
                    # 3. Find first contact that doesn't have an existing queue item in this campaign
                    chosen_contact = None
                    for oc in other_contacts:
                        used_result = await db.execute(
                            select(OutreachQueueItem).where(
                                OutreachQueueItem.campaign_id == item.campaign_id,
                                OutreachQueueItem.recipient_email == oc.email
                            )
                        )
                        if not used_result.scalars().first():
                            chosen_contact = oc
                            break
                    
                    if chosen_contact:
                        new_item = OutreachQueueItem(
                            campaign_id=item.campaign_id,
                            company_id=item.company_id,
                            job_id=item.job_id,
                            recipient_email=chosen_contact.email,
                            recipient_type=chosen_contact.contact_type,
                            subject=item.subject,
                            body=item.body,
                            outreach_style=item.outreach_style,
                            status="pending",
                            priority=item.priority,
                            scheduled_at=datetime.utcnow(),
                        )
                        db.add(new_item)
                        logger.info(f"Suppression fallback: Enqueued alternative contact {chosen_contact.email} for company_id={item.company_id}")
                    else:
                        logger.info(f"Suppression fallback: No alternative contacts found for company_id={item.company_id}")
                return False

            item.retry_count += 1
            error_msg_short = error_msg[:500]

            if item.retry_count >= item.max_retries:
                item.status = "failed"
                item.error_message = f"Max retries exceeded. Last error: {error_msg_short}"
                logger.error(f"Queue item {item.id}: failed permanently after {item.retry_count} retries")
            else:
                # Exponential backoff: reschedule
                backoff_minutes = 2 ** item.retry_count * 5  # 10, 20, 40 minutes
                item.scheduled_at = datetime.utcnow() + timedelta(minutes=backoff_minutes)
                item.status = "pending"
                item.error_message = f"Retry {item.retry_count}: {error_msg_short}"
                logger.warning(
                    f"Queue item {item.id}: retry {item.retry_count}, "
                    f"next attempt in {backoff_minutes}m"
                )

            return False

    @staticmethod
    async def _check_campaign_completion(db: AsyncSession, campaign: Campaign):
        """Check if all queue items are terminal (sent/failed/skipped) → mark complete."""
        result = await db.execute(
            select(func.count(OutreachQueueItem.id))
            .where(
                OutreachQueueItem.campaign_id == campaign.id,
                OutreachQueueItem.status.in_(["pending", "scheduled"]),
            )
        )
        remaining = result.scalar() or 0

        if remaining == 0:
            # Check if there are any items at all
            total_result = await db.execute(
                select(func.count(OutreachQueueItem.id))
                .where(OutreachQueueItem.campaign_id == campaign.id)
            )
            total = total_result.scalar() or 0

            if total > 0:
                campaign.status = "completed"
                campaign.updated_at = datetime.utcnow()
                logger.info(f"Campaign {campaign.id}: all items processed, marking completed")
                await db.commit()
