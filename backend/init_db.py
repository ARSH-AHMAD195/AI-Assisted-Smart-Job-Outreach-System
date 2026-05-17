import asyncio
from app.database import engine, Base
from app.models import User, JobListing, CompanyProfile, OutreachEmail, TrackingEvent

async def init_db():
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
