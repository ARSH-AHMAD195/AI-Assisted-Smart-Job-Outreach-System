from pydantic import BaseModel, HttpUrl
from typing import Optional, List

class CompanyBase(BaseModel):
    name: str
    website: Optional[HttpUrl] = None
    industry: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    recent_news: Optional[str] = None
    hiring_roles: Optional[List[str]] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    website: Optional[HttpUrl] = None
    industry: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    recent_news: Optional[str] = None
    hiring_roles: Optional[List[str]] = None


class CompanyResponse(CompanyBase):
    id: int

    class Config:
        from_attributes = True