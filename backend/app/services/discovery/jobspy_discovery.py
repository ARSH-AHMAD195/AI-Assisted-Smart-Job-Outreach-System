import logging
from typing import List
from datetime import datetime
import pandas as pd
from jobspy import scrape_jobs
from app.schemas.job_intelligence import BaseJobListing, EnrichedJob
from app.services.enrichment.enrichment_service import EnrichmentService
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class JobSpyDiscoveryService:
    @staticmethod
    async def _warm_session(context, site_url: str):
        """
        Navigate to the site to establish fresh cookies and session state.
        """
        page = await context.new_page()
        session_data = {"cookies": {}, "headers": {}}
        
        try:
            logger.info(f"Warming session for {site_url}...")
            await page.goto(site_url, wait_until="domcontentloaded", timeout=30000)
            
            cookies = await context.cookies()
            session_data["cookies"] = {c['name']: c['value'] for c in cookies}
            return session_data
        except Exception as e:
            logger.error(f"Failed to warm session for {site_url}: {e}")
            return session_data
        finally:
            await page.close()

    @staticmethod
    async def discover_and_enrich(role: str, location: str = "India", limit: int = 5) -> List[EnrichedJob]:
        """
        Discover jobs using JobSpy (with Session Warming) and enrich them.
        """
        try:
            # 1. Warm up session using Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ]
                import random
                selected_ua = random.choice(user_agents)
                context = await browser.new_context(user_agent=selected_ua)
                
                # Warm up Indeed & LinkedIn
                indeed_session = await JobSpyDiscoveryService._warm_session(context, "https://in.indeed.com/")
                linkedin_session = await JobSpyDiscoveryService._warm_session(context, "https://www.linkedin.com/jobs")
                
                logger.info(f"JobSpy: Scraping jobs for {role} in {location}...")
                
                from app.utils.proxy_handler import ProxyHandler
                proxies = ProxyHandler.get_jobspy_proxies()
                
                # 2. Scrape jobs using JobSpy
                all_jobs_dfs = []
                
                # LinkedIn Scrape
                try:
                    df_linkedin = scrape_jobs(
                        site_name=["linkedin"],
                        search_term=role,
                        location=location,
                        results_wanted=limit,
                        extra_headers=linkedin_session["headers"],
                        extra_cookies=linkedin_session["cookies"],
                        proxies=proxies
                    )
                    if not df_linkedin.empty: all_jobs_dfs.append(df_linkedin)
                except Exception as e:
                    logger.error(f"LinkedIn scrape failed: {e}")

                # Indeed Scrape
                try:
                    df_indeed = scrape_jobs(
                        site_name=["indeed"],
                        search_term=role,
                        location=location,
                        results_wanted=limit,
                        country_indeed="india",
                        hours_old=72,
                        extra_headers=indeed_session["headers"],
                        extra_cookies=indeed_session["cookies"],
                        proxies=proxies
                    )
                    if not df_indeed.empty: all_jobs_dfs.append(df_indeed)
                except Exception as e:
                    logger.error(f"Indeed scrape failed: {e}")

                # Google Jobs Scrape
                try:
                    df_google = scrape_jobs(
                        site_name=["google"],
                        search_term=f"{role} in {location}",
                        results_wanted=limit,
                        proxies=proxies
                    )
                    if not df_google.empty: all_jobs_dfs.append(df_google)
                except Exception as e:
                    logger.error(f"Google Jobs scrape failed: {e}")

                # Glassdoor Scrape
                try:
                    df_glassdoor = scrape_jobs(
                        site_name=["glassdoor"],
                        search_term=role,
                        location=location,
                        results_wanted=limit,
                        proxies=proxies
                    )
                    if not df_glassdoor.empty: all_jobs_dfs.append(df_glassdoor)
                except Exception as e:
                    logger.error(f"Glassdoor scrape failed: {e}")

                if not all_jobs_dfs:
                    logger.warning("JobSpy returned no jobs from any board.")
                    return []
                
                jobs_df = pd.concat(all_jobs_dfs, ignore_index=True)
                
                # Filter out anti-bot results
                if not jobs_df.empty:
                    jobs_df = jobs_df[~jobs_df['title'].str.contains('Security Check|hCaptcha|Cloudflare', case=False, na=False)]
                    jobs_df = jobs_df[~jobs_df['company'].str.contains('Security Check|Indeed', case=False, na=False)]
                    
                if jobs_df.empty:
                    logger.warning("All scraped jobs were anti-bot checks.")
                    return []
            
            # 2. Map JobSpy output to BaseJobListing
            base_listings = []
            for _, row in jobs_df.iterrows():
                # Extract emails if present (JobSpy sometimes finds them)
                raw_emails = row.get('emails', '')
                email_list = []
                if raw_emails and isinstance(raw_emails, str):
                    email_list = [e.strip() for e in raw_emails.split(',')]

                base_listings.append(BaseJobListing(
                    job_id=str(row.get('id', '')),
                    title=str(row.get('title', 'Unknown Title')),
                    company=str(row.get('company', 'Unknown Company')),
                    location=str(row.get('location', 'Remote')),
                    link=str(row.get('job_url', '')),
                    description=str(row.get('description', '')),
                    emails=email_list,
                    tags=str(row.get('skills', '')).split(',') if row.get('skills') else [],
                    platform=str(row.get('site', 'JobSpy'))
                ))
            
            # 3. Enrich each listing using our Playwright-based pipeline
            enriched_jobs = []
            async with async_playwright() as p:
                from app.utils.proxy_handler import ProxyHandler
                proxy_config = ProxyHandler.get_playwright_proxy()
                
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    proxy=proxy_config if proxy_config else None
                )
                
                for base_job in base_listings:
                    if not base_job.link: continue
                    try:
                        enriched = await EnrichmentService.enrich_job_listing(context, base_job)
                        enriched_jobs.append(enriched)
                    except Exception as e:
                        logger.error(f"Enrichment failed for {base_job.link}: {e}")
                        from app.schemas.job_intelligence import JobIntelligence, CompanyProfile, CompanySignals
                        enriched_jobs.append(EnrichedJob(
                            base_job_listing=base_job,
                            job_intelligence=JobIntelligence(title=base_job.title),
                            company_profile=CompanyProfile(company_name=base_job.company),
                            company_signals=CompanySignals(),
                            scraped_at=datetime.now()
                        ))
                
                await browser.close()
                
            return enriched_jobs

        except Exception as e:
            logger.error(f"JobSpy Discovery failed: {e}")
            return []
