import asyncio
from app.database import engine, get_db
from app.models import CompanyProfile, JobListing, CompanyContact, OutreachQueueItem
from sqlalchemy import select

async def check_db():
    print("Checking database objects for TechDoQuest:")
    async for db in get_db():
        # Check JobListing
        job_res = await db.execute(select(JobListing).where(JobListing.company_name.ilike("%TechDoQuest%")))
        jobs = job_res.scalars().all()
        print(f"\nJobs found ({len(jobs)}):")
        for j in jobs:
            print(f"- Job ID: {j.id}, Title: {j.title}, Company: {j.company_name}, Url: {j.job_url}")

        # Check CompanyProfile
        comp_res = await db.execute(select(CompanyProfile).where(CompanyProfile.name.ilike("%TechDoQuest%")))
        companies = comp_res.scalars().all()
        print(f"\nCompanies found ({len(companies)}):")
        for c in companies:
            print(f"- Company ID: {c.id}, Name: {c.name}, Website: {c.website}, Careers Email: {c.careers_email}")

            # Check Contacts for this company
            contact_res = await db.execute(select(CompanyContact).where(CompanyContact.company_id == c.id))
            contacts = contact_res.scalars().all()
            print(f"  Contacts found ({len(contacts)}):")
            for ct in contacts:
                print(f"  - Contact ID: {ct.id}, Name: {ct.name}, Email: {ct.email}, Role: {ct.role}, Type: {ct.contact_type}")

        # Check Queue items
        queue_res = await db.execute(select(OutreachQueueItem))
        items = queue_res.scalars().all()
        print(f"\nTotal OutreachQueueItems in database: {len(items)}")
        for item in items:
            print(f"- Item ID: {item.id}, Campaign ID: {item.campaign_id}, Recipient: {item.recipient_email}, Status: {item.status}")

if __name__ == "__main__":
    asyncio.run(check_db())
