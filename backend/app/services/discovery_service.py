import logging
from typing import List
from app.schemas.job import JobListing as JobSchema
from app.schemas.job_intelligence import EnrichedJob
from app.services.discovery.jobspy_discovery import JobSpyDiscoveryService

logger = logging.getLogger(__name__)

class DiscoveryService:
    @staticmethod
    async def discover_jobs(role: str, location: str = "India") -> List[JobSchema]:
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
    async def discover_enriched_jobs(role: str, location: str = "India") -> List[EnrichedJob]:
        """Expose the full enriched intelligence to the application."""
        return await JobSpyDiscoveryService.discover_and_enrich(role, location, limit=5)
