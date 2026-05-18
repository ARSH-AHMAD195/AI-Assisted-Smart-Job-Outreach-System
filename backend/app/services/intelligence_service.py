import trafilatura
from app.models import CompanyProfile
from typing import Optional
import os
import json
import logging

logger = logging.getLogger(__name__)

class IntelligenceService:
    @staticmethod
    async def enrich_company(company_name: str, website_url: Optional[str] = None) -> Optional[dict]:
        """
        Enrich company profile by scraping their website and using LLM for summary.
        """
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

            return intel
        except Exception as e:
            logger.error(f"Intelligence extraction error: {e}")
            return None
