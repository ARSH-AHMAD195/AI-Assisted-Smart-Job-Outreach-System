import asyncio
from app.database import AsyncSessionLocal, engine, Base
from app.models import User, JobListing, CompanyProfile, OutreachEmail, TrackingEvent
from datetime import datetime, timedelta

async def seed_data():
    async with AsyncSessionLocal() as db:
        # 1. Clear existing data
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        print("Seeding database...")

        # 2. Seed Users
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

        # 3. Seed Job Listings
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

        # 4. Seed Company Profiles
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

        # 5. Seed Outreach Emails
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

        # 6. Seed Tracking Events
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

        await db.commit()
        print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
