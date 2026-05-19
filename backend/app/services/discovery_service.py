import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import JobListing as DBJobListing
from app.schemas.job import JobListing as JobSchema
from app.schemas.job_intelligence import EnrichedJob
from app.services.discovery.jobspy_discovery import JobSpyDiscoveryService

logger = logging.getLogger(__name__)

class DiscoveryService:
    @staticmethod
    async def discover_jobs(db: AsyncSession, role: str, location: str = "India") -> List[JobSchema]:
        """
        Discover jobs using JobSpy + Intelligence pipeline.
        Maps EnrichedJob back to the base JobListing for backward compatibility.
        """
        try:
            logger.info(f"Starting JobSpy discovery for {role} in {location}")
            
            # Use the new JobSpy discovery engine
            enriched_results = await JobSpyDiscoveryService.discover_and_enrich(role, location, limit=5)
            
            if not enriched_results:
                logger.warning("No live results found. Falling back to demo data.")
                return DiscoveryService._get_demo_data(role, location)
            
            # Map EnrichedJob -> JobSchema
            listings = []
            for enriched in enriched_results:
                # Prioritize enriched responsibilities, then base description
                final_description = enriched.job_intelligence.responsibilities or enriched.base_job_listing.description or "No description available."
                
                listings.append(JobSchema(
                    title=enriched.job_intelligence.title or enriched.base_job_listing.title,
                    company=enriched.base_job_listing.company or enriched.company_profile.company_name,
                    location=enriched.base_job_listing.location,
                    description=final_description,
                    job_url=enriched.base_job_listing.link,
                    emails=enriched.base_job_listing.emails
                ))
            
            # Save discovered jobs to the database
            for item in listings:
                try:
                    if item.job_url:
                        query = select(DBJobListing).where(DBJobListing.job_url == item.job_url)
                        res = await db.execute(query)
                        exists = res.scalars().first()
                        if not exists:
                            db_job = DBJobListing(
                                title=item.title,
                                company_name=item.company,
                                location=item.location,
                                description=item.description,
                                job_url=item.job_url,
                                source="JobSpy"
                            )
                            db.add(db_job)
                            logger.info(f"Pushed newly discovered job to database: {item.title} at {item.company}")
                except Exception as dbe:
                    logger.warning(f"Error persisting discovered job to DB: {dbe}")

            try:
                await db.commit()
            except Exception as commite:
                logger.warning(f"Error committing job listings to database: {commite}")

            return listings

        except Exception as e:
            logger.error(f"Discovery Service error: {e}")
            return DiscoveryService._get_demo_data(role, location)

    @staticmethod
    def _get_demo_data(role: str, location: str) -> List[JobSchema]:
        return [
            JobSchema(
                title=f"Senior {role} (Demo)",
                company="TechCorp",
                location=location,
                description="This is a demo result shown when live scraping is restricted or fails.",
                job_url="https://example.com/demo1"
            )
        ]

    @staticmethod
    async def discover_enriched_jobs(db: AsyncSession, role: str, location: str = "India") -> List[EnrichedJob]:
        """Expose the full enriched intelligence to the application and persist listings."""
        enriched_results = await JobSpyDiscoveryService.discover_and_enrich(role, location, limit=5)
        for enriched in enriched_results:
            try:
                url = enriched.base_job_listing.link
                if url:
                    query = select(DBJobListing).where(DBJobListing.job_url == url)
                    res = await db.execute(query)
                    exists = res.scalars().first()
                    if not exists:
                        final_description = enriched.job_intelligence.responsibilities or enriched.base_job_listing.description or "No description available."
                        db_job = DBJobListing(
                            title=enriched.job_intelligence.title or enriched.base_job_listing.title,
                            company_name=enriched.base_job_listing.company or enriched.company_profile.company_name,
                            location=enriched.base_job_listing.location,
                            description=final_description,
                            job_url=url,
                            source="JobSpy"
                        )
                        db.add(db_job)
                        logger.info(f"Pushed newly discovered enriched job to database: {db_job.title} at {db_job.company_name}")
            except Exception as dbe:
                logger.warning(f"Error persisting enriched job to DB: {dbe}")
        
        try:
            await db.commit()
        except Exception as commite:
            logger.warning(f"Error committing enriched job listings to database: {commite}")
            
        return enriched_results
