from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database.session import Base
from datetime import datetime

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
