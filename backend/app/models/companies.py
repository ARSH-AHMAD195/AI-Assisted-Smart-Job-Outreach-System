from sqlalchemy import Column, Integer, String, Text, JSON
from database.session import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    company_email = Column(String, nullable=True)

    tech_stack = Column(JSON, nullable=True)
    recent_news = Column(Text, nullable=True)
    hiring_roles = Column(JSON, nullable=True)