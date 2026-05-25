"""
Contacts Router — REST endpoints for contact discovery and management.

Endpoints:
    POST   /api/contacts/discover              → Trigger contact discovery for a company
    GET    /api/contacts/company/{company_id}   → List discovered contacts for a company
    GET    /api/contacts/{id}                   → Contact detail
    PUT    /api/contacts/{id}                   → Update contact metadata
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contact import CompanyContact
from app.schemas.contact import (
    ContactDiscoveryRequest,
    ContactDiscoveryResult,
    ContactResponse,
    ContactUpdateRequest,
)
from app.services.contact_discovery_service import ContactDiscoveryService

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


@router.post("/discover", response_model=ContactDiscoveryResult)
async def discover_contacts(
    payload: ContactDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger contact discovery for a company.
    Crawls career pages, about pages, and contact pages to find
    publicly available email addresses.
    """
    try:
        result = await ContactDiscoveryService.discover_contacts(
            db=db,
            company_name=payload.company_name,
            website_url=payload.website_url,
            company_id=payload.company_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Contact discovery failed: {str(e)}",
        )


@router.get("/company/{company_id}", response_model=list[ContactResponse])
async def get_contacts_for_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all discovered contacts for a company, ordered by confidence score."""
    contacts = await ContactDiscoveryService.get_contacts_for_company(db, company_id)
    return [
        ContactResponse(
            id=c.id,
            company_id=c.company_id,
            email=c.email,
            contact_type=c.contact_type,
            source=c.source,
            confidence_score=c.confidence_score,
            is_verified=c.is_verified,
            last_contacted_at=c.last_contacted_at,
            contact_count=c.contact_count,
            created_at=c.created_at,
            name=c.name,
            role=c.role,
        )
        for c in contacts
    ]


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single contact's details."""
    result = await db.execute(
        select(CompanyContact).where(CompanyContact.id == contact_id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return ContactResponse(
        id=contact.id,
        company_id=contact.company_id,
        email=contact.email,
        contact_type=contact.contact_type,
        source=contact.source,
        confidence_score=contact.confidence_score,
        is_verified=contact.is_verified,
        last_contacted_at=contact.last_contacted_at,
        contact_count=contact.contact_count,
        created_at=contact.created_at,
        name=contact.name,
        role=contact.role,
    )


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    payload: ContactUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a contact's metadata (type, verification, score)."""
    result = await db.execute(
        select(CompanyContact).where(CompanyContact.id == contact_id)
    )
    contact = result.scalars().first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if payload.contact_type is not None:
        contact.contact_type = payload.contact_type
    if payload.is_verified is not None:
        contact.is_verified = payload.is_verified
    if payload.confidence_score is not None:
        contact.confidence_score = payload.confidence_score

    await db.commit()
    await db.refresh(contact)

    return ContactResponse(
        id=contact.id,
        company_id=contact.company_id,
        email=contact.email,
        contact_type=contact.contact_type,
        source=contact.source,
        confidence_score=contact.confidence_score,
        is_verified=contact.is_verified,
        last_contacted_at=contact.last_contacted_at,
        contact_count=contact.contact_count,
        created_at=contact.created_at,
        name=contact.name,
        role=contact.role,
    )
