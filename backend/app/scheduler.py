from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.discovery_service import DiscoveryService
from app.database import AsyncSessionLocal
from app.models import JobListing
from sqlalchemy.future import select

scheduler = AsyncIOScheduler()

async def discovery_job():
    """Periodic job to discover new listings."""
    # Example: Discover jobs for a set of common roles
    roles = ["Backend Developer", "Machine Learning Engineer", "Frontend Developer"]
    for role in roles:
        print(f"[Scheduler] Discovering jobs for {role}...")
        jobs = await DiscoveryService.discover_jobs(role)
        
        async with AsyncSessionLocal() as db:
            for job in jobs:
                # Check if job already exists
                stmt = select(JobListing).where(JobListing.job_url == job.job_url)
                result = await db.execute(stmt)
                if not result.scalar():
                    db_job = JobListing(
                        title=job.title,
                        company_name=job.company,
                        location=job.location,
                        description=job.description,
                        job_url=job.job_url,
                        source="Discovery"
                    )
                    db.add(db_job)
            await db.commit()

def start_scheduler():
    # Add discovery job every 6 hours
    scheduler.add_job(discovery_job, 'interval', hours=6)
    scheduler.start()
    print("Scheduler started.")
