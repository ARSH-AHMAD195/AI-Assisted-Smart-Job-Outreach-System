from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class JobIntelligence(BaseModel):
    title: str
    responsibilities: Optional[str] = None
    educational_requirements: Optional[str] = None
    technical_requirements: Optional[str] = None
    preferred_skills: Optional[str] = None
    role: Optional[str] = None
    industry: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    experience: Optional[str] = None
    key_skills: List[str] = []

class CompanyProfile(BaseModel):
    company_name: Optional[str] = "N/A"
    vision: Optional[str] = None
    products: List[str] = []
    tech_stack: List[str] = []
    engineering_culture: Optional[str] = None
    overview: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    industry_tags: List[str] = []
    company_tags: List[str] = []
    culture_keywords: List[str] = []
    address: Optional[str] = None
    ai_focus: bool = False
    cloud_focus: bool = False
    digital_transformation_focus: bool = False

class CompanySignals(BaseModel):
    culture_signals: List[str] = []
    awards: List[str] = []
    recognitions: List[str] = []
    benefits: List[str] = []
    review_snippets: List[str] = []
    salary_insights: Optional[str] = None
    perks: List[str] = []

class BaseJobListing(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    link: str
    description: Optional[str] = None
    emails: List[str] = []
    tags: List[str] = []
    platform: str = "JobSpy"

class EnrichedJob(BaseModel):
    base_job_listing: BaseJobListing
    job_intelligence: JobIntelligence
    company_profile: CompanyProfile
    company_signals: CompanySignals
    outreach_email: Optional[str] = None
    scraped_at: datetime = datetime.now()
