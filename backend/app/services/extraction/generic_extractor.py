import logging
from playwright.async_api import Page
from app.schemas.job_intelligence import JobIntelligence, CompanyProfile, CompanySignals

logger = logging.getLogger(__name__)

class GenericExtractor:
    @staticmethod
    async def extract_job_intelligence(page: Page) -> JobIntelligence:
        """
        Generic job intelligence extraction with email discovery.
        """
        try:
            title = await page.title()
            
            # 1. Extract Description
            description = await page.evaluate("""() => {
                const selectors = ['article', 'main', '#jobDescriptionText', '.jobsearch-JobComponent-description', '.description'];
                for (const s of selectors) {
                    const el = document.querySelector(s);
                    if (el && el.innerText.length > 200) return el.innerText;
                }
                return document.body.innerText;
            }""")

            # 2. Extract emails from text
            emails = await page.evaluate(r"""() => {
                const text = document.body.innerText;
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
                return Array.from(new Set(text.match(emailRegex) || []));
            }""")

            return JobIntelligence(
                title=title,
                responsibilities=description,
                tech_stack=[],
                key_skills=emails, # Use key_skills to carry emails for now
                role_requirements=description[:500] + "..." if description else "N/A"
            )
        except Exception as e:
            logger.error(f"Generic extraction failed: {e}")
            return JobIntelligence(title="N/A")

    @staticmethod
    async def extract_company_profile(page: Page) -> CompanyProfile:
        try:
            title = await page.title()
            # If the title contains " - ", try to extract the company name (common in Indeed/LinkedIn)
            # e.g. "Software Engineer - TechCorp - Remote" -> TechCorp
            company_name = "N/A"
            if " - " in title:
                parts = title.split(" - ")
                if len(parts) > 1:
                    company_name = parts[1].strip()
            
            emails = await page.evaluate(r"""() => {
                const text = document.body.innerText;
                const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
                return Array.from(new Set(text.match(emailRegex) || []));
            }""")
            
            return CompanyProfile(
                company_name=company_name,
                email=emails[0] if emails else None
            )
        except:
            return CompanyProfile(company_name="N/A")

    @staticmethod
    async def extract_company_signals(page: Page) -> CompanySignals:
        return CompanySignals()
