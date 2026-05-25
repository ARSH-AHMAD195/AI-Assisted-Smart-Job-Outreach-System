"""
Pydantic schemas for the Contact Discovery layer.

Defines request/response models for discovering, classifying,
and managing public company contact channels.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# --- Discovery Request ---

class ContactDiscoveryRequest(BaseModel):
    """Request to trigger contact discovery for a company."""
    company_name: str
    website_url: Optional[str] = None
    company_id: Optional[int] = None  # If already in DB


# --- Discovered Contact ---

class DiscoveredContact(BaseModel):
    """A single discovered contact channel."""
    email: str
    contact_type: str = Field(
        description="Type of contact: careers, recruiting, hr, engineering, founder"
    )
    source: str = Field(
        description="Where this contact was found: careers_page, about_page, contact_page, job_listing"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Reliability score based on source and email pattern"
    )
    name: Optional[str] = None
    role: Optional[str] = None


class ContactDiscoveryResult(BaseModel):
    """Result of a contact discovery operation."""
    company_name: str
    company_id: Optional[int] = None
    contacts: List[DiscoveredContact] = []
    discovery_timestamp: str
    total_pages_scraped: int = 0


# --- Contact Response (DB-backed) ---

class ContactResponse(BaseModel):
    """Response for a stored company contact."""
    id: int
    company_id: int
    email: str
    contact_type: str
    source: Optional[str] = None
    confidence_score: float
    is_verified: bool
    last_contacted_at: Optional[datetime] = None
    contact_count: int
    created_at: datetime
    name: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True


class ContactUpdateRequest(BaseModel):
    """Request to update a contact's metadata."""
    contact_type: Optional[str] = None
    is_verified: Optional[bool] = None
    confidence_score: Optional[float] = None
