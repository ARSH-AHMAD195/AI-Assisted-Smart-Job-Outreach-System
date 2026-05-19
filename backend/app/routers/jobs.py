from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.inference_service import InferenceService
from app.services.discovery_service import DiscoveryService
from app.schemas.user import FinalUserProfile
from typing import List

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("/infer-roles")
async def infer_roles(profile: FinalUserProfile):
    """Infer relevant roles from candidate profile."""
    roles = await InferenceService.infer_roles(profile)
    return roles

@router.get("/discover")
async def discover_jobs(role: str, location: str = "Remote", db: AsyncSession = Depends(get_db)):
    """Discover jobs for a specific role and location."""
    jobs = await DiscoveryService.discover_jobs(db, role, location)
    return jobs

@router.get("/discover-enriched")
async def discover_enriched_jobs(role: str, location: str = "Remote", db: AsyncSession = Depends(get_db)):
    """Discover and deeply enrich jobs for a specific role and location."""
    jobs = await DiscoveryService.discover_enriched_jobs(db, role, location)
    return jobs
