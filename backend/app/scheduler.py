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


async def outreach_queue_job():
    """
    Periodic job to process the outreach queue.
    Runs every 5 minutes, processing pending items for all active campaigns
    while respecting rate limits, company caps, and stagger intervals.
    """
    from app.services.outreach_queue_service import OutreachQueueService

    print("[Scheduler] Processing outreach queue...")
    async with AsyncSessionLocal() as db:
        try:
            await OutreachQueueService.process_queue(db)
        except Exception as e:
            print(f"[Scheduler] Outreach queue error: {e}")


async def optimization_job():
    """
    Daily adaptive optimization.
    Updates behavioral confidence scores, aggregates strategy performance,
    and decays stale contacts.
    """
    from app.services.adaptive_optimizer_service import AdaptiveOptimizerService

    print("[Scheduler] Running daily optimization...")
    async with AsyncSessionLocal() as db:
        try:
            await AdaptiveOptimizerService.run_daily_optimization(db)
        except Exception as e:
            print(f"[Scheduler] Optimization error: {e}")


def start_scheduler():
    # Add discovery job every 6 hours
    scheduler.add_job(discovery_job, 'interval', hours=6)
    # Add outreach queue processor every 5 minutes
    scheduler.add_job(outreach_queue_job, 'interval', minutes=5)
    # Add daily optimization job
    scheduler.add_job(optimization_job, 'interval', hours=24)
    scheduler.start()
    print("Scheduler started (discovery: 6h, outreach queue: 5m, optimization: 24h).")

