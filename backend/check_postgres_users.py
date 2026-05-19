import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.database import Base
from app.models import User, JobListing, CompanyProfile, OutreachEmail, TrackingEvent
from datetime import datetime

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    DATABASE_URL, 
    connect_args={"prepared_statement_cache_size": 0, "statement_cache_size": 0},
    echo=True
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def seed_supabase_direct():
    print("=== STARTING DIRECT SUPABASE SCHEMA CREATION & SEEDING ===")
    
    # 1. Create tables one-by-one in dependency order to bypass visibility issues
    # Alter existing users table to add profile_data JSON column if not exists
    print("Ensuring 'profile_data' column exists on 'users' table...")
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SET search_path TO public"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data JSON"))
        print("✓ Altered 'users' table or column already exists.")
    except Exception as e:
        print(f"✗ Warning altering 'users' table: {e}")

    # Dependency order of creation
    table_order = ["users", "job_listings", "company_profiles", "outreach_emails", "tracking_events"]
    
    for name in table_order:
        table = Base.metadata.tables.get(name)
        if table is not None:
            print(f"Creating table '{name}'...")
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SET search_path TO public"))
                    await conn.run_sync(lambda connection: table.create(connection))
                print(f"✓ Table '{name}' created successfully.")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"✓ Table '{name}' already exists (skipping creation).")
                else:
                    print(f"✗ Error creating table '{name}': {e}")

    # 2. Seed data
    async with AsyncSessionLocal() as db:
        print("\nSeeding data into remote Supabase database...")

        # We will check if the user is already seeded by email
        from sqlalchemy import select
        user_res = await db.execute(select(User).where(User.email == "om@example.com"))
        existing_user = user_res.scalars().first()
        
        if not existing_user:
            user = User(
                full_name="Om Anand",
                email="om@example.com",
                password_hash="pbkdf2:sha256:600000$defaultseededhash",
                profile_data={
                    "name": "Om Anand",
                    "email": "om@example.com",
                    "phone": "1234567890",
                    "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "React"],
                    "projects": [
                        {
                            "title": "Job Outreach System",
                            "description": ["Built an AI-powered system for job outreach using FastAPI and Llama 3."]
                        }
                    ],
                    "experience": [],
                    "education": []
                }
            )
            db.add(user)
            print("✓ User added to seed.")

        # Job Listings seed
        job_res = await db.execute(select(JobListing).where(JobListing.job_url == "https://careers.google.com/jobs/123"))
        existing_job = job_res.scalars().first()
        if not existing_job:
            jobs = [
                JobListing(
                    title="Senior Backend Engineer",
                    company_name="Google",
                    location="Mountain View, CA",
                    description="We are looking for a senior backend engineer to join our cloud team. Experience with Python and distributed systems is required.",
                    job_url="https://careers.google.com/jobs/123",
                    source="LinkedIn"
                ),
                JobListing(
                    title="AI Research Scientist",
                    company_name="OpenAI",
                    location="San Francisco, CA",
                    description="Join us in building safe and beneficial AI. Expertise in LLMs and PyTorch is a must.",
                    job_url="https://openai.com/careers/456",
                    source="Direct"
                ),
                JobListing(
                    title="Fullstack Developer",
                    company_name="Stripe",
                    location="Remote",
                    description="Help us build the future of payments. Proficiency in React and Ruby on Rails/Python preferred.",
                    job_url="https://stripe.com/jobs/789",
                    source="Indeed"
                )
            ]
            for job in jobs:
                db.add(job)
            print("✓ Job listings added to seed.")

        # Company Profiles seed
        company_res = await db.execute(select(CompanyProfile).where(CompanyProfile.name == "Google"))
        existing_company = company_res.scalars().first()
        if not existing_company:
            companies = [
                CompanyProfile(
                    name="Google",
                    website="https://google.com",
                    vision="To organize the world's information and make it universally accessible and useful.",
                    engineering_culture="Data-driven, collaborative, and focused on scale.",
                    tech_stack=["C++", "Python", "Go", "Java", "TensorFlow"]
                ),
                CompanyProfile(
                    name="OpenAI",
                    website="https://openai.com",
                    vision="To ensure that artificial general intelligence benefits all of humanity.",
                    engineering_culture="Rapid iteration, research-focused, and safety-conscious.",
                    tech_stack=["Python", "PyTorch", "Kubernetes"]
                )
            ]
            for company in companies:
                db.add(company)
            print("✓ Company profiles added to seed.")

        # Outreach Emails seed
        # Flush session state to assign primary keys to User and JobListing
        await db.flush()

        # Retrieve active user_id
        db_user = existing_user if existing_user else user
        u_id = db_user.user_id

        # Resolve job listing IDs
        google_job_id = None
        openai_job_id = None
        stripe_job_id = None

        job_query = await db.execute(select(JobListing))
        for jl in job_query.scalars().all():
            if jl.company_name == "Google":
                google_job_id = jl.id
            elif jl.company_name == "OpenAI":
                openai_job_id = jl.id
            elif jl.company_name == "Stripe":
                stripe_job_id = jl.id

        # Outreach Emails seed
        email_res = await db.execute(select(OutreachEmail).where(OutreachEmail.transactional_id == "t_12345"))
        existing_email = email_res.scalars().first()
        if not existing_email:
            outreach1 = OutreachEmail(
                transactional_id="t_12345",
                recipient_email="hiring@google.com",
                subject="Personalized Outreach - Om Anand",
                body="Hi, I noticed your opening for a Senior Backend Engineer. I've built several AI systems using FastAPI...",
                strategy="project-focused",
                status="OPENED",
                user_id=u_id,
                job_id=google_job_id
            )
            outreach2 = OutreachEmail(
                transactional_id="t_67890",
                recipient_email="jobs@openai.com",
                subject="Passionate about AI Safety - Om Anand",
                body="Hello, I'm a huge fan of OpenAI's mission. My recent project involves using Llama 3 for intelligent outreach...",
                strategy="curiosity-driven",
                status="REPLIED",
                user_id=u_id,
                job_id=openai_job_id
            )
            outreach3 = OutreachEmail(
                transactional_id="t_11121",
                recipient_email="recruiter@stripe.com",
                subject="Backend Developer - Om Anand",
                body="Hi, I'm reaching out regarding the Fullstack Developer role. I have extensive experience with Python and React...",
                strategy="skill-focused",
                status="SENT",
                user_id=u_id,
                job_id=stripe_job_id
            )
            db.add(outreach1)
            db.add(outreach2)
            db.add(outreach3)
            print("✓ Outreach emails with relational user/job binding added to seed.")

        # Tracking Events seed
        event_res = await db.execute(select(TrackingEvent).where(TrackingEvent.transactional_id == "t_12345"))
        existing_event = event_res.scalars().first()
        if not existing_event:
            events = [
                TrackingEvent(
                    transactional_id="t_12345",
                    event_type="OPEN",
                    payload={"email": "hiring@google.com"}
                ),
                TrackingEvent(
                    transactional_id="t_67890",
                    event_type="OPEN",
                    payload={"email": "jobs@openai.com"}
                ),
                TrackingEvent(
                    transactional_id="t_67890",
                    event_type="REPLY",
                    payload={"email": "jobs@openai.com"}
                )
            ]
            for event in events:
                db.add(event)
            print("✓ Tracking events added to seed.")

        try:
            await db.commit()
            print("=== SUCCESS: SUPABASE DATABASE SEEDED SUCCESSFULLY! ===")
        except Exception as e:
            print(f"Error committing Supabase seeds: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_supabase_direct())
