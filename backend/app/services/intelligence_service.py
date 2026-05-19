import trafilatura
from app.models import CompanyProfile
from typing import Optional
import os
import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class IntelligenceService:
    @staticmethod
    async def enrich_company(db: AsyncSession, company_name: str, website_url: Optional[str] = None) -> Optional[dict]:
        """
        Enrich company profile by checking database first (caching layer), 
        then scraping website and using LLM if not found.
        """
        # 1. Check DB Cache
        try:
            query = select(CompanyProfile).where(CompanyProfile.name.ilike(company_name))
            if website_url:
                clean_url = website_url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
                query = select(CompanyProfile).where(
                    (CompanyProfile.name.ilike(company_name)) | 
                    (CompanyProfile.website.ilike(f"%{clean_url}%"))
                )
            res = await db.execute(query)
            cached = res.scalars().first()
            if cached:
                logger.info(f"Database Cache HIT for company: {company_name}")
                return {
                    "vision": cached.vision,
                    "products": cached.products or [],
                    "tech_stack": cached.tech_stack or [],
                    "engineering_culture": cached.engineering_culture
                }
        except Exception as e:
            logger.warning(f"Error checking cache: {e}")

        logger.info(f"Database Cache MISS for company: {company_name}. Crawling...")
        if not website_url:
            # Default to .com if no URL is provided
            clean_name = "".join(filter(str.isalnum, company_name.lower()))
            website_url = f"https://{clean_name}.com"
            
        from app.utils.proxy_handler import ProxyHandler
        import requests
        
        proxies = ProxyHandler.get_jobspy_proxies()
        proxy_dict = {"https": proxies[0], "http": proxies[0]} if proxies else None
        
        try:
            response = requests.get(website_url, proxies=proxy_dict, timeout=15)
            downloaded = response.text if response.ok else None
        except:
            downloaded = None
            
        if not downloaded:
            return None
            
        content = trafilatura.extract(downloaded)
        if not content:
            return None
            
        from app.utils.ai_handler import AIHandler
        
        # Use LLM to extract structured intelligence from the raw content
        system_prompt = "You are a Company Intelligence Expert. Analyze website content and extract: vision, products, engineering culture, and technical stack."
        prompt = f"""
        Analyze the following text extracted from {company_name}'s website.
        
        WEBSITE CONTENT (Truncated):
        {content[:10000]}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "vision": "...",
            "products": ["...", "..."],
            "tech_stack": ["...", "..."],
            "engineering_culture": "..."
        }}
        """
        
        try:
            result_text = await AIHandler.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                provider="gemini"
            )
            
            # Extract JSON from text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            intel = json.loads(result_text)
            
            # Ensure tech_stack is a list
            if isinstance(intel.get("tech_stack"), str):
                intel["tech_stack"] = [s.strip() for s in intel["tech_stack"].split(",")]
            elif not isinstance(intel.get("tech_stack"), list):
                intel["tech_stack"] = []

            # Ensure products is a list
            if isinstance(intel.get("products"), str):
                intel["products"] = [s.strip() for s in intel["products"].split(",")]
            elif not isinstance(intel.get("products"), list):
                intel["products"] = []

            # Save newly crawled intel to the database for future caching
            try:
                new_profile = CompanyProfile(
                    name=company_name,
                    website=website_url,
                    vision=intel.get("vision", ""),
                    products=intel.get("products", []),
                    tech_stack=intel.get("tech_stack", []),
                    engineering_culture=intel.get("engineering_culture", "")
                )
                db.add(new_profile)
                await db.commit()
                logger.info(f"Successfully saved newly enriched company to database: {company_name}")
            except Exception as dbe:
                logger.warning(f"Failed to persist newly crawled company profile: {dbe}")

            return intel
        except Exception as e:
            logger.error(f"Intelligence extraction error: {e}")
            return None
