import csv
import re
import os
from typing import List, Dict, Optional
from app.schemas.contact import DiscoveredContact

class CSVContactService:
    """Service to query and match company contacts from local HR contacts CSV file."""
    
    CSV_PATH = "hr_contacts.csv"

    @classmethod
    def clean_company_name(cls, name: str) -> str:
        """Normalize company name by lowering case, stripping whitespace, and removing common suffixes."""
        if not name:
            return ""
        name = name.lower().strip()
        suffixes = [
            "technologies", "technology", "solutions", "software", "services", "labs",
            "inc.", "inc", "ltd.", "ltd", "pvt.", "pvt", "co.", "co", "gmbh", "limited",
            "corp.", "corp", "corporation", "india"
        ]
        for s in suffixes:
            name = re.sub(r'\b' + re.escape(s) + r'\b', '', name)
        # Remove all non-alphanumeric characters
        return "".join(filter(str.isalnum, name))

    @classmethod
    def lookup_contacts(cls, company_name: str) -> List[Dict]:
        """Search the local CSV for any contacts matching the company name."""
        if not os.path.exists(cls.CSV_PATH):
            return []

        target_clean = cls.clean_company_name(company_name)
        if not target_clean:
            return []

        matches = []
        with open(cls.CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_company = row.get("Company", "")
                csv_clean = cls.clean_company_name(csv_company)
                
                if not csv_clean:
                    continue
                    
                # Match criteria: Exact match after cleaning, or substring matching for safety
                if target_clean == csv_clean:
                    matches.append(row)
                elif len(target_clean) > 3 and target_clean in csv_clean:
                    matches.append(row)
                elif len(csv_clean) > 3 and csv_clean in target_clean:
                    matches.append(row)
        return matches

    @classmethod
    def classify_csv_contact_type(cls, title: str, email: str) -> str:
        """Classify contact type based on the title or email prefix."""
        title_lower = title.lower() if title else ""
        email_lower = email.lower() if email else ""

        if any(kw in title_lower for kw in ["founder", "ceo", "cto", "co-founder"]):
            return "founder"
        if any(kw in title_lower for kw in ["engineering", "tech", "developer", "architect"]):
            return "engineering"
        if any(kw in title_lower for kw in ["recruiter", "talent", "ta"]):
            return "recruiting"
        if any(kw in title_lower for kw in ["hr", "human resource", "people", "culture"]):
            return "hr"

        # Fallback to email prefix analysis
        if "recruit" in email_lower:
            return "recruiting"
        if "hr" in email_lower or "people" in email_lower:
            return "hr"
        if "founder" in email_lower or "ceo" in email_lower:
            return "founder"
        
        return "hr" # Default for HR contacts CSV
