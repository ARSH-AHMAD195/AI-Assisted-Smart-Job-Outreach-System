import asyncio
import csv
from urllib.parse import urlparse
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import CompanyProfile
from app.models.contact import CompanyContact
from app.services.csv_contact_service import CSVContactService

async def import_contacts():
    csv_path = "hr_contacts.csv"
    print(f"Reading contacts from {csv_path}...")
    
    async with AsyncSessionLocal() as db:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        print(f"Total contacts in CSV: {len(rows)}")
        imported_count = 0
        skipped_count = 0
        
        # Batch size for performance
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            
            for row in batch:
                name = row.get("Name", "").strip()
                email = row.get("Email", "").strip()
                title = row.get("Title", "").strip()
                company_name = row.get("Company", "").strip()
                
                if not email or not company_name:
                    skipped_count += 1
                    continue
                
                # 1. Look up or create CompanyProfile
                comp_result = await db.execute(
                    select(CompanyProfile).where(CompanyProfile.name.ilike(f"%{company_name}%"))
                )
                company = comp_result.scalars().first()
                
                if not company:
                    # Parse domain from email for a better website URL fallback
                    email_domain = email.split("@")[-1].lower() if "@" in email else ""
                    website_url = f"https://{email_domain}" if email_domain else f"https://{CSVContactService.clean_company_name(company_name)}.com"
                    
                    company = CompanyProfile(
                        name=company_name,
                        website=website_url,
                        vision="Profile generated during contact import.",
                        products=[],
                        tech_stack=[],
                        engineering_culture=""
                    )
                    db.add(company)
                    await db.flush() # Flush to populate company.id
                
                # 2. Check if contact already exists
                contact_result = await db.execute(
                    select(CompanyContact).where(
                        CompanyContact.company_id == company.id,
                        CompanyContact.email == email
                    )
                )
                existing_contact = contact_result.scalars().first()
                
                if not existing_contact:
                    contact_type = CSVContactService.classify_csv_contact_type(title, email)
                    db_contact = CompanyContact(
                        company_id=company.id,
                        email=email,
                        contact_type=contact_type,
                        source="csv_import",
                        confidence_score=0.95,
                        is_verified=True,
                        name=name,
                        role=title
                    )
                    db.add(db_contact)
                    imported_count += 1
                else:
                    # Update name/role if they were empty
                    if not existing_contact.name:
                        existing_contact.name = name
                    if not existing_contact.role:
                        existing_contact.role = title
                    skipped_count += 1
            
            # Commit after each batch
            await db.commit()
            print(f"Processed {min(i+batch_size, len(rows))}/{len(rows)}: Imported {imported_count}, Skipped {skipped_count}")

    print("CSV contact import finished successfully!")

if __name__ == "__main__":
    asyncio.run(import_contacts())
