"""
Campaign Service — manages campaign lifecycle and queue population.

Handles creating campaigns, discovering contacts for target jobs,
generating strategy-variant emails, and enqueuing outreach items.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CompanyProfile, JobListing
from app.models.campaign import Campaign, OutreachQueueItem
from app.models.contact import CompanyContact
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    QueueStatusResponse,
)
from app.services.contact_discovery_service import ContactDiscoveryService

logger = logging.getLogger(__name__)


class CampaignService:
    """Manages campaign lifecycle: create, populate, start, pause, complete."""

    @staticmethod
    async def create_campaign(
        db: AsyncSession,
        user_id: str,
        payload: CampaignCreate,
    ) -> Campaign:
        """Create a new outreach campaign with delivery settings."""
        campaign = Campaign(
            user_id=user_id,
            name=payload.name,
            target_role=payload.target_role,
            max_emails_per_hour=payload.max_emails_per_hour,
            max_contacts_per_company=payload.max_contacts_per_company,
            stagger_interval_minutes=payload.stagger_interval_minutes,
            status="draft",
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        logger.info(f"Created campaign '{campaign.name}' (id={campaign.id}) for user={user_id}")
        return campaign

    @staticmethod
    async def get_campaign(db: AsyncSession, campaign_id: int) -> Optional[Campaign]:
        """Retrieve a campaign by ID."""
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_campaigns(db: AsyncSession, user_id: str) -> List[Campaign]:
        """List all campaigns for a user."""
        result = await db.execute(
            select(Campaign)
            .where(Campaign.user_id == user_id)
            .order_by(Campaign.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_campaign(
        db: AsyncSession,
        campaign_id: int,
        payload: CampaignUpdate,
    ) -> Optional[Campaign]:
        """Update campaign settings."""
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if not campaign:
            return None

        if payload.name is not None:
            campaign.name = payload.name
        if payload.max_emails_per_hour is not None:
            campaign.max_emails_per_hour = payload.max_emails_per_hour
        if payload.max_contacts_per_company is not None:
            campaign.max_contacts_per_company = payload.max_contacts_per_company
        if payload.stagger_interval_minutes is not None:
            campaign.stagger_interval_minutes = payload.stagger_interval_minutes

        campaign.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def set_campaign_status(
        db: AsyncSession,
        campaign_id: int,
        status: str,
    ) -> Optional[Campaign]:
        """Set campaign status (draft, active, paused, completed)."""
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if not campaign:
            return None

        campaign.status = status
        campaign.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(campaign)
        logger.info(f"Campaign {campaign_id} status → {status}")
        return campaign

    @staticmethod
    async def delete_campaign(db: AsyncSession, campaign_id: int) -> bool:
        """Delete a campaign and all its queue items."""
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if not campaign:
            return False

        await db.delete(campaign)
        await db.commit()
        logger.info(f"Deleted campaign {campaign_id}")
        return True

    @staticmethod
    async def populate_queue(
        db: AsyncSession,
        campaign_id: int,
        job_ids: List[int],
        user_profile_summary: Optional[str] = None,
    ) -> QueueStatusResponse:
        """
        Populate the outreach queue for a campaign:
        1. For each job → look up company
        2. Discover contacts for the company
        3. Generate strategy-variant emails per contact
        4. Enqueue items with staggered scheduling
        """
        campaign = await CampaignService.get_campaign(db, campaign_id)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        from app.services.variant_generator_service import VariantGeneratorService

        items_created = 0
        stagger_offset = 0

        for job_id in job_ids:
            # 1. Look up the job
            job_result = await db.execute(
                select(JobListing).where(JobListing.id == job_id)
            )
            job = job_result.scalars().first()
            if not job:
                logger.warning(f"Job {job_id} not found, skipping")
                continue

            # 2. Find or create company profile
            company_result = await db.execute(
                select(CompanyProfile).where(
                    CompanyProfile.name.ilike(f"%{job.company_name}%")
                )
            )
            company = company_result.scalars().first()

            company_id = company.id if company else None

            # 3. Discover contacts for the company
            contacts = []
            if company_id:
                contacts = await ContactDiscoveryService.get_contacts_for_company(db, company_id)

            if not contacts and company:
                # Run discovery
                discovery_result = await ContactDiscoveryService.discover_contacts(
                    db=db,
                    company_name=job.company_name,
                    website_url=company.website if company else None,
                    company_id=company_id,
                )
                # Re-fetch from DB after discovery
                if company_id:
                    contacts = await ContactDiscoveryService.get_contacts_for_company(db, company_id)

            # If no contacts found, use the company_email or careers_email as fallback
            if not contacts:
                fallback_email = None
                if company and company.careers_email:
                    fallback_email = company.careers_email
                elif hasattr(company, 'company_email') if company else False:
                    fallback_email = getattr(company, 'company_email', None)

                if not fallback_email:
                    if company and company.website:
                        from urllib.parse import urlparse
                        domain = urlparse(company.website).netloc.replace("www.", "")
                        if domain:
                            fallback_email = f"hiring@{domain}"
                    if not fallback_email:
                        clean_name = "".join(filter(str.isalnum, job.company_name.lower()))
                        fallback_email = f"hiring@{clean_name}.com"

                if fallback_email:
                    # Create a queue item with the fallback email
                    variant = await VariantGeneratorService.generate_single_variant(
                        recipient_type="careers",
                        company_name=job.company_name,
                        job_title=job.title,
                        job_description=job.description or "",
                        company_intel={
                            "vision": company.vision if company else None,
                            "products": company.products if company else [],
                            "tech_stack": company.tech_stack if company else [],
                            "engineering_culture": company.engineering_culture if company else None,
                        } if company else None,
                        user_profile_summary=user_profile_summary,
                    )

                    scheduled_time = datetime.utcnow() + timedelta(
                        minutes=stagger_offset * campaign.stagger_interval_minutes
                    )

                    queue_item = OutreachQueueItem(
                        campaign_id=campaign_id,
                        company_id=company_id,
                        job_id=job_id,
                        recipient_email=fallback_email,
                        recipient_type="careers",
                        subject=variant["subject"],
                        body=variant["body"],
                        outreach_style=variant["style"],
                        status="pending",
                        priority=5,
                        scheduled_at=scheduled_time,
                    )
                    db.add(queue_item)
                    items_created += 1
                    stagger_offset += 1
                continue

            # 4. Limit contacts per company cap
            max_contacts = campaign.max_contacts_per_company
            selected_contacts = contacts[:max_contacts]

            # 5. Generate variant for each contact and enqueue
            for contact in selected_contacts:
                try:
                    variant = await VariantGeneratorService.generate_single_variant(
                        recipient_type=contact.contact_type,
                        company_name=job.company_name,
                        job_title=job.title,
                        job_description=job.description or "",
                        company_intel={
                            "vision": company.vision if company else None,
                            "products": company.products if company else [],
                            "tech_stack": company.tech_stack if company else [],
                            "engineering_culture": company.engineering_culture if company else None,
                        } if company else None,
                        user_profile_summary=user_profile_summary,
                        recipient_name=getattr(contact, "name", None),
                        recipient_role=getattr(contact, "role", None),
                    )

                    scheduled_time = datetime.utcnow() + timedelta(
                        minutes=stagger_offset * campaign.stagger_interval_minutes
                    )

                    queue_item = OutreachQueueItem(
                        campaign_id=campaign_id,
                        contact_id=contact.id,
                        company_id=company_id,
                        job_id=job_id,
                        recipient_email=contact.email,
                        recipient_type=contact.contact_type,
                        subject=variant["subject"],
                        body=variant["body"],
                        outreach_style=variant["style"],
                        status="pending",
                        priority=5,
                        scheduled_at=scheduled_time,
                    )
                    db.add(queue_item)
                    items_created += 1
                    stagger_offset += 1

                except Exception as e:
                    logger.error(f"Failed to generate variant for {contact.email}: {e}")

        await db.commit()
        logger.info(f"Populated campaign {campaign_id} with {items_created} queue items")

        return await CampaignService.get_queue_status(db, campaign_id)

    @staticmethod
    async def get_queue_status(db: AsyncSession, campaign_id: int) -> QueueStatusResponse:
        """Get aggregated queue status for a campaign."""
        result = await db.execute(
            select(
                OutreachQueueItem.status,
                func.count(OutreachQueueItem.id)
            )
            .where(OutreachQueueItem.campaign_id == campaign_id)
            .group_by(OutreachQueueItem.status)
        )
        counts = {row[0]: row[1] for row in result.all()}

        return QueueStatusResponse(
            campaign_id=campaign_id,
            total=sum(counts.values()),
            pending=counts.get("pending", 0),
            scheduled=counts.get("scheduled", 0),
            sent=counts.get("sent", 0),
            failed=counts.get("failed", 0),
            skipped=counts.get("skipped", 0),
        )

    @staticmethod
    async def get_queue_items(
        db: AsyncSession,
        campaign_id: int,
        status_filter: Optional[str] = None,
    ) -> List[OutreachQueueItem]:
        """Get queue items for a campaign, optionally filtered by status."""
        query = select(OutreachQueueItem).where(
            OutreachQueueItem.campaign_id == campaign_id
        )
        if status_filter:
            query = query.where(OutreachQueueItem.status == status_filter)

        query = query.order_by(OutreachQueueItem.scheduled_at.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_campaign_response(db: AsyncSession, campaign: Campaign) -> CampaignResponse:
        """Build a CampaignResponse with aggregated counts."""
        queue_status = await CampaignService.get_queue_status(db, campaign.id)
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            status=campaign.status,
            target_role=campaign.target_role,
            max_emails_per_hour=campaign.max_emails_per_hour,
            max_contacts_per_company=campaign.max_contacts_per_company,
            stagger_interval_minutes=campaign.stagger_interval_minutes,
            queue_size=queue_status.total,
            sent_count=queue_status.sent,
            failed_count=queue_status.failed,
            pending_count=queue_status.pending,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
