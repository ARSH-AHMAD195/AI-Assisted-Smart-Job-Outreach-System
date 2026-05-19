from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.intelligence_service import IntelligenceService
from typing import Optional

router = APIRouter(prefix="/api/company", tags=["Company"])

@router.get("/enrich")
async def enrich_company(name: str, url: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Enrich company data from website."""
    intel = await IntelligenceService.enrich_company(db, name, url)
    if not intel:
        raise HTTPException(status_code=404, detail="Could not enrich company intelligence.")
    return intel
