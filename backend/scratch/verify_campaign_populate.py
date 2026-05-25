import asyncio
from app.database import engine, get_db
from app.models import Campaign, JobListing, CompanyProfile, OutreachQueueItem, User
from app.services.campaign_service import CampaignService
from sqlalchemy import select

async def verify_populate():
    print("=== CAMPAIGN POPULATION VERIFICATION ===")
    async for db in get_db():
        # Get or create User
        user_res = await db.execute(select(User).limit(1))
        user = user_res.scalars().first()
        if not user:
            user = User(
                user_id="test_populate_uid_123",
                full_name="Populate Tester",
                email="pop_test@example.com"
            )
            db.add(user)
            await db.commit()
            print("Created test user.")

        # Create a test Campaign
        campaign = Campaign(
            user_id=user.user_id,
            name="Verify Populate Campaign",
            target_role="Full Stack Developer",
            status="paused",
            max_emails_per_hour=2,
            max_contacts_per_company=3,
            stagger_interval_minutes=120
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        print(f"Created Campaign ID: {campaign.id}")

        # Create a JobListing
        job = JobListing(
            title="Full Stack Developer",
            company_name="TechDoQuest",
            job_url="https://techdoquest.com/jobs/123",
            source="LinkedIn",
            description="We need someone to build cool stuff."
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        print(f"Created Job ID: {job.id}")

        # Ensure CompanyProfile exists but has no careers_email or contacts
        company_res = await db.execute(select(CompanyProfile).where(CompanyProfile.name == "TechDoQuest"))
        company = company_res.scalars().first()
        if not company:
            company = CompanyProfile(
                name="TechDoQuest",
                website="https://techdoquest.com",
                vision="To do quests in tech.",
                tech_stack=["Python"]
            )
            db.add(company)
            await db.commit()
            await db.refresh(company)
        else:
            company.careers_email = None
            db.add(company)
            await db.commit()
            print("Cleared company careers email.")

        print("Populating queue for campaign...")
        # Populate the campaign
        response = await CampaignService.populate_queue(
            db=db,
            campaign_id=campaign.id,
            job_ids=[job.id],
            user_profile_summary="Senior Dev with 5 years exp."
        )
        print(f"Response: {response}")

        # Check queue items
        q_res = await db.execute(select(OutreachQueueItem).where(OutreachQueueItem.campaign_id == campaign.id))
        queue_items = q_res.scalars().all()
        print(f"\nGenerated Queue Items ({len(queue_items)}):")
        for item in queue_items:
            print(f"- Recipient: {item.recipient_email}, Subject: {item.subject}, Body preview: {item.body[:60]}...")

        # Assert at least one item was created
        assert len(queue_items) > 0, "No queue items were generated!"
        print("✓ SUCCESS: Fallback queue item successfully enqueued!")

        # Clean up
        for item in queue_items:
            await db.delete(item)
        await db.delete(campaign)
        await db.delete(job)
        await db.commit()
        print("Cleaned up database records.")

if __name__ == "__main__":
    asyncio.run(verify_populate())
