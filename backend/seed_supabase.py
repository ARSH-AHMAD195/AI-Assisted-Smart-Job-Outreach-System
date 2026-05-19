import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import User, JobListing, CompanyProfile, OutreachEmail, TrackingEvent
from datetime import datetime

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment!")

connect_args = {}
if DATABASE_URL.startswith("postgresql"):
    connect_args = {
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0
    }
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"Connecting to remote database: {DATABASE_URL.split('@')[-1]}")

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

from sqlalchemy import text

async def seed_supabase():
    print("=== STARTING SUPABASE DATABASE MIGRATION & SEEDING ===")
    
    # 1. Create tables on Supabase if they do not exist
    async with engine.begin() as conn:
        print("Setting search path to public schema...")
        await conn.execute(text("SET search_path TO public"))
        print("Creating tables on remote Supabase instance if they don't exist...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables verified/created successfully.")

    # 2. Seed data
    async with AsyncSessionLocal() as db:
        print("\nSeeding Supabase data...")

        # Clear old seeded data first if necessary, or check before insert
        # We will add default records with fallback checks
        
        # User seed
        user = User(
            name="Om Anand",
            email="om@example.com",
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

        # Job Listings seed
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

        # Company Profiles seed
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

        # Outreach Emails seed
        outreach1 = OutreachEmail(
            transactional_id="t_12345",
            recipient_email="hiring@google.com",
            subject="Personalized Outreach - Om Anand",
            body="Hi, I noticed your opening for a Senior Backend Engineer. I've built several AI systems using FastAPI...",
            strategy="project-focused",
            status="OPENED"
        )
        outreach2 = OutreachEmail(
            transactional_id="t_67890",
            recipient_email="jobs@openai.com",
            subject="Passionate about AI Safety - Om Anand",
            body="Hello, I'm a huge fan of OpenAI's mission. My recent project involves using Llama 3 for intelligent outreach...",
            strategy="curiosity-driven",
            status="REPLIED"
        )
        outreach3 = OutreachEmail(
            transactional_id="t_11121",
            recipient_email="recruiter@stripe.com",
            subject="Backend Developer - Om Anand",
            body="Hi, I'm reaching out regarding the Fullstack Developer role. I have extensive experience with Python and React...",
            strategy="skill-focused",
            status="SENT"
        )
        db.add(outreach1)
        db.add(outreach2)
        db.add(outreach3)

        # Tracking Events seed
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

        try:
            await db.commit()
            print("✓ Supabase database seeded successfully!")
        except Exception as e:
            print(f"Error seeding Supabase: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(seed_supabase())
