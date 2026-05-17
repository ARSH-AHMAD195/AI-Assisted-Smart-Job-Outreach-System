import logging
from typing import Dict
from playwright.async_api import BrowserContext
from app.schemas.job_intelligence import EnrichedJob, BaseJobListing, CompanyProfile, JobIntelligence, CompanySignals
from app.services.extraction.generic_extractor import GenericExtractor
from datetime import datetime

from app.utils.retry_helper import async_retry

logger = logging.getLogger(__name__)

class EnrichmentService:
    # In-memory cache for company profiles to optimize scraping
    _company_cache: Dict[str, CompanyProfile] = {}

    @classmethod
    @async_retry(retries=3, delay=2)
    async def _safe_goto(cls, page, url):
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    @classmethod
    async def enrich_job_listing(cls, context: BrowserContext, base_job: BaseJobListing) -> EnrichedJob:
        """
        Enrich a base job listing by navigating to its detail page and extracting deep intelligence.
        """
        page = await context.new_page()
        # Set a realistic user agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })
        
        try:
            logger.info(f"Enriching job: {base_job.title} at {base_job.company}")
            
            # 1. Select Extractor (Naukri removed)
            extractor = GenericExtractor
            
            # 2. Navigate to job detail page with retry
            await cls._safe_goto(page, base_job.link)
            
            # 3. Extract Job Intelligence
            # First check if we're blocked by Cloudflare
            title = await page.title()
            if "Cloudflare" in title or "Security Check" in title or "Just a moment" in title:
                logger.warning(f"Anti-bot detected for {base_job.link}. Falling back to base description.")
                job_intel = JobIntelligence(title=base_job.title, responsibilities=base_job.description or "Blocked by anti-bot.")
            else:
                job_intel = await extractor.extract_job_intelligence(page)
            
            # Merge extracted emails into base_job (key_skills carries them from generic_extractor)
            if job_intel.key_skills:
                extracted_emails = [s for s in job_intel.key_skills if "@" in s]
                base_job.emails = list(set(base_job.emails + extracted_emails))
                logger.info(f"Merged {len(extracted_emails)} extracted emails into base job.")

            # Fallback to base description if extraction is sparse
            if (not job_intel.responsibilities or len(job_intel.responsibilities) < 100) and base_job.description:
                job_intel.responsibilities = base_job.description
                logger.info(f"Using base description fallback for {base_job.title}")

            # 4. Extract Company Profile (with caching)
            company_name = base_job.company.strip().lower()
            if company_name in cls._company_cache:
                logger.info(f"Using cached company profile for: {base_job.company}")
                company_profile = cls._company_cache[company_name]
            else:
                company_profile = await extractor.extract_company_profile(page)
                if company_profile.company_name != "N/A":
                    cls._company_cache[company_name] = company_profile
            
            # 5. Extract Company Signals
            company_signals = await extractor.extract_company_signals(page)
            
            enriched = EnrichedJob(
                base_job_listing=base_job,
                job_intelligence=job_intel,
                company_profile=company_profile,
                company_signals=company_signals,
                outreach_email=base_job.emails[0] if base_job.emails else None,
                scraped_at=datetime.now()
            )
            
            return enriched
            
        except Exception as e:
            logger.info(f"Using fallback enrichment for {base_job.link}: {e}")
            # Return a minimally enriched job on failure instead of crashing the pipeline
            return EnrichedJob(
                base_job_listing=base_job,
                job_intelligence=JobIntelligence(
                    title=base_job.title,
                    responsibilities=base_job.description or "No description available."
                ),
                company_profile=CompanyProfile(company_name=base_job.company),
                company_signals=CompanySignals(),
                outreach_email=base_job.emails[0] if base_job.emails else None,
                scraped_at=datetime.now()
            )
        finally:
            await page.close()
