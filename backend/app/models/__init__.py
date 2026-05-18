from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    profile_data = Column(JSON)  # Stores the full FinalUserProfile
    created_at = Column(DateTime, default=datetime.utcnow)

class JobListing(Base):
    __tablename__ = "job_listings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company_name = Column(String, index=True)
    location = Column(String)
    description = Column(Text)
    tech_stack = Column(JSON)
    job_url = Column(String, unique=True)
    source = Column(String)  # e.g., 'LinkedIn', 'Wellfound'
    created_at = Column(DateTime, default=datetime.utcnow)

class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    website = Column(String)
    vision = Column(Text)
    products = Column(JSON)
    tech_stack = Column(JSON)
    engineering_culture = Column(Text)
    careers_email = Column(String)
    last_enriched = Column(DateTime, default=datetime.utcnow)

class OutreachEmail(Base):
    __tablename__ = "outreach_emails"
    id = Column(Integer, primary_key=True, index=True)
    transactional_id = Column(String, unique=True, index=True)
    recipient_email = Column(String, index=True)
    subject = Column(String)
    body = Column(Text)
    strategy = Column(String)
    status = Column(String, default="SENT")  # SENT, OPENED, REPLIED, BOUNCED
    job_id = Column(Integer, ForeignKey("job_listings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)

class TrackingEvent(Base):
    __tablename__ = "tracking_events"
    id = Column(Integer, primary_key=True, index=True)
    transactional_id = Column(String, index=True)
    event_type = Column(String)  # OPEN, CLICK, REPLY, BOUNCE
    timestamp = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON)
