import asyncio
import logging
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import CompanyProfile
from app.services.contact_discovery_service import ContactDiscoveryService
from app.services.variant_generator_service import VariantGeneratorService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_test():
    company_name = "SourceFuse"
    print(f"\n==========================================")
    print(f"TESTING INTEGRATION FOR: {company_name}")
    print(f"==========================================")
    
    async with AsyncSessionLocal() as db:
        # 1. Clean existing contacts for SourceFuse to ensure clean discovery
        # Find company
        comp_res = await db.execute(
            select(CompanyProfile).where(CompanyProfile.name.ilike(f"%{company_name}%"))
        )
        company = comp_res.scalars().first()
        company_id = company.id if company else None
        
        # 2. Trigger contact discovery (should hit CSV)
        print(f"Triggering contact discovery for {company_name}...")
        discovery_result = await ContactDiscoveryService.discover_contacts(
            db=db,
            company_name=company_name,
            company_id=company_id
        )
        
        print(f"\nDiscovery Results:")
        print(f"- Pages Scraped: {discovery_result.total_pages_scraped} (Expected 0 due to CSV hit)")
        print(f"- Contacts Found: {len(discovery_result.contacts)}")
        
        for c in discovery_result.contacts:
            print(f"  * Name: {c.name}, Email: {c.email}, Role: {c.role}, Type: {c.contact_type}")
        
        if not discovery_result.contacts:
            print("No contacts found. Make sure the import script has processed SourceFuse.")
            return

        # 3. Generate a personalized email variant for the first contact
        first_contact = discovery_result.contacts[0]
        print(f"\nGenerating email variant for {first_contact.name} ({first_contact.role})...")
        
        variant = await VariantGeneratorService.generate_single_variant(
            recipient_type=first_contact.contact_type,
            company_name=company_name,
            job_title="Full Stack Engineer",
            job_description="We are looking for a Python developer with FastAPI and React experience.",
            company_intel={
                "vision": "To build next generation enterprise cloud applications.",
                "tech_stack": ["Python", "FastAPI", "React", "AWS"],
                "products": ["Cloud-native portal"]
            },
            user_profile_summary="Om is a backend developer with 2 years of experience in FastAPI and cloud computing.",
            recipient_name=first_contact.name,
            recipient_role=first_contact.role
        )
        
        print(f"\nGenerated Email Subject:")
        print(variant.get("subject"))
        print(f"\nGenerated Email Body:")
        print(variant.get("body"))
        print(f"\nPersonalization Points:")
        for pt in variant.get("personalization_points", []):
            print(f"- {pt}")

if __name__ == "__main__":
    asyncio.run(run_test())
