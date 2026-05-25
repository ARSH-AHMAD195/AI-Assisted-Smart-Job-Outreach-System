"""
Contact Discovery Service — discovers publicly available contact channels for companies.

Uses Playwright to crawl company career pages, about pages, contact pages,
and job listings to extract email addresses. Classifies each email by type
(careers, recruiting, hr, engineering, founder) and assigns a confidence score.

Flow:
    1. Receive company_name + optional website_url
    2. Derive target URLs (careers page, about page, contact page)
    3. Crawl each page via Playwright, extract emails from text + mailto: links
    4. Classify each email by type using pattern matching
    5. Assign confidence scores based on source reliability + email pattern
    6. Deduplicate and store in company_contacts table
    7. Return ContactDiscoveryResult
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from playwright.async_api import async_playwright, Page

from app.models import CompanyProfile
from app.models.contact import CompanyContact
from app.schemas.contact import DiscoveredContact, ContactDiscoveryResult

logger = logging.getLogger(__name__)


# Email regex pattern — matches standard email addresses
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE
)

# Emails to exclude (common false positives)
EXCLUDED_PATTERNS = re.compile(
    r'(example\.com|test\.com|placeholder|noreply@|no-reply@|'
    r'support@|admin@|webmaster@|postmaster@|mailer-daemon@|'
    r'\.png$|\.jpg$|\.gif$|\.svg$|\.css$|\.js$)',
    re.IGNORECASE
)


class ContactDiscoveryService:
    """Discovers publicly available contact channels for companies."""

    # Email prefix → (contact_type, base_confidence_score) mapping
    CONTACT_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
        (re.compile(r'^careers?@', re.I),               "careers",    0.92),
        (re.compile(r'^recruit(ing|ment)?@', re.I),     "recruiting", 0.90),
        (re.compile(r'^hr@|^human.?resources?@', re.I), "hr",         0.88),
        (re.compile(r'^hiring@|^jobs?@|^talent@', re.I),"careers",    0.87),
        (re.compile(r'^engineer(ing)?@|^tech@|^dev(eloper)?@', re.I),
                                                        "engineering",0.85),
        (re.compile(r'^founder@|^ceo@|^cto@', re.I),   "founder",    0.80),
        (re.compile(r'^people@|^culture@', re.I),       "hr",         0.82),
        (re.compile(r'^team@', re.I),                   "careers",    0.75),
        (re.compile(r'^hello@|^hi@', re.I),             "careers",    0.60),
        (re.compile(r'^info@|^contact@', re.I),         "careers",    0.55),
    ]

    # Common subpaths to scrape for contact information
    DISCOVERY_PATHS = [
        "/careers",
        "/jobs",
        "/about",
        "/contact",
        "/team",
        "/about-us",
        "/contact-us",
        "/join-us",
        "/work-with-us",
    ]

    # Source URL pattern → source label + confidence boost
    SOURCE_SCORING: List[Tuple[re.Pattern, str, float]] = [
        (re.compile(r'/careers?|/jobs?|/hiring', re.I),  "careers_page",  0.10),
        (re.compile(r'/about|/team|/people', re.I),      "about_page",    0.05),
        (re.compile(r'/contact', re.I),                  "contact_page",  0.03),
    ]

    @classmethod
    async def discover_contacts(
        cls,
        db: AsyncSession,
        company_name: str,
        website_url: Optional[str] = None,
        company_id: Optional[int] = None,
    ) -> ContactDiscoveryResult:
        """
        Discover public contact channels for a company.

        Args:
            db: Database session
            company_name: Company name to search for
            website_url: Optional company website URL
            company_id: Optional existing company_profiles.id

        Returns:
            ContactDiscoveryResult with discovered contacts
        """
        logger.info(f"Starting contact discovery for: {company_name}")

        # 1. Resolve company profile + website
        profile = None
        if company_id:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.id == company_id)
            )
            profile = result.scalars().first()

        if not profile and company_name:
            result = await db.execute(
                select(CompanyProfile).where(
                    CompanyProfile.name.ilike(f"%{company_name}%")
                )
            )
            profile = result.scalars().first()

        if profile and not website_url:
            website_url = profile.website

        if not website_url:
            # Derive from company name
            clean_name = "".join(filter(str.isalnum, company_name.lower()))
            website_url = f"https://{clean_name}.com"

        # Normalize URL
        if not website_url.startswith("http"):
            website_url = f"https://{website_url}"

        # 1.5 Check local CSV database for pre-existing HR contacts
        from app.services.csv_contact_service import CSVContactService
        csv_matches = CSVContactService.lookup_contacts(company_name)
        if csv_matches:
            logger.info(f"Found {len(csv_matches)} contacts in local CSV for {company_name}")
            csv_contacts = []
            for row in csv_matches:
                csv_contacts.append(
                    DiscoveredContact(
                        email=row["Email"],
                        contact_type=CSVContactService.classify_csv_contact_type(row.get("Title", ""), row["Email"]),
                        source="csv_lookup",
                        confidence_score=0.95,
                        name=row.get("Name"),
                        role=row.get("Title")
                    )
                )

            # Persist to database
            resolved_company_id = profile.id if profile else company_id
            if resolved_company_id:
                await cls._persist_contacts(db, resolved_company_id, csv_contacts)

            return ContactDiscoveryResult(
                company_name=company_name,
                company_id=resolved_company_id,
                contacts=csv_contacts,
                discovery_timestamp=datetime.utcnow().isoformat(),
                total_pages_scraped=0,
            )

        # 2. Crawl pages and extract emails
        all_contacts: List[DiscoveredContact] = []
        pages_scraped = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )

            # Scrape the base URL first
            base_contacts = await cls._scrape_page_emails(context, website_url)
            all_contacts.extend(base_contacts)
            pages_scraped += 1

            # Scrape discovery paths
            base_domain = urlparse(website_url).scheme + "://" + urlparse(website_url).netloc
            for path in cls.DISCOVERY_PATHS:
                target_url = urljoin(base_domain, path)
                try:
                    page_contacts = await cls._scrape_page_emails(context, target_url)
                    all_contacts.extend(page_contacts)
                    pages_scraped += 1
                except Exception as e:
                    logger.debug(f"Failed to scrape {target_url}: {e}")

            await browser.close()

        # 3. Deduplicate by email
        seen_emails = set()
        unique_contacts: List[DiscoveredContact] = []
        for contact in sorted(all_contacts, key=lambda c: c.confidence_score, reverse=True):
            email_lower = contact.email.lower()
            if email_lower not in seen_emails:
                seen_emails.add(email_lower)
                unique_contacts.append(contact)

        # 4. Filter: only keep emails whose domain matches the company website
        company_domain = urlparse(website_url).netloc.replace("www.", "")
        filtered_contacts = []
        for contact in unique_contacts:
            email_domain = contact.email.split("@")[-1].lower()
            # Accept if email domain contains the company domain or vice versa
            if (company_domain in email_domain) or (email_domain in company_domain):
                filtered_contacts.append(contact)
            else:
                logger.debug(f"Filtered out off-domain email: {contact.email}")

        # 5. Persist to database
        resolved_company_id = profile.id if profile else company_id
        if resolved_company_id and filtered_contacts:
            await cls._persist_contacts(db, resolved_company_id, filtered_contacts)

        result = ContactDiscoveryResult(
            company_name=company_name,
            company_id=resolved_company_id,
            contacts=filtered_contacts,
            discovery_timestamp=datetime.utcnow().isoformat(),
            total_pages_scraped=pages_scraped,
        )

        logger.info(
            f"Contact discovery complete for {company_name}: "
            f"{len(filtered_contacts)} contacts from {pages_scraped} pages"
        )
        return result

    @classmethod
    async def _scrape_page_emails(
        cls,
        context,
        url: str,
    ) -> List[DiscoveredContact]:
        """
        Navigate to a URL and extract email addresses from page content
        and mailto: links.
        """
        contacts = []
        page = await context.new_page()

        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            if not response or response.status >= 400:
                logger.debug(f"Non-OK response for {url}: {response.status if response else 'None'}")
                return contacts

            # Check for anti-bot pages
            title = await page.title()
            if any(kw in title for kw in ["Cloudflare", "Security Check", "Just a moment", "hCaptcha"]):
                logger.debug(f"Anti-bot detected at {url}")
                return contacts

            # Extract emails from page text content
            text_content = await page.inner_text("body")
            text_emails = EMAIL_REGEX.findall(text_content)

            # Extract emails from mailto: links
            mailto_emails = await page.eval_on_selector_all(
                'a[href^="mailto:"]',
                """elements => elements.map(el => {
                    const href = el.getAttribute('href') || '';
                    return href.replace('mailto:', '').split('?')[0].trim();
                })"""
            )

            all_emails = set(text_emails + mailto_emails)

            # Determine source label from URL
            source_label = "website"
            source_boost = 0.0
            for pattern, label, boost in cls.SOURCE_SCORING:
                if pattern.search(url):
                    source_label = label
                    source_boost = boost
                    break

            # Classify each email
            for email in all_emails:
                email = email.strip().lower()

                # Skip excluded patterns
                if EXCLUDED_PATTERNS.search(email):
                    continue

                # Skip obviously invalid emails
                if len(email) < 5 or ".." in email:
                    continue

                contact = cls._classify_email(email, source_label, source_boost)
                contacts.append(contact)

        except Exception as e:
            logger.debug(f"Error scraping {url}: {e}")
        finally:
            await page.close()

        return contacts

    @classmethod
    def _classify_email(
        cls,
        email: str,
        source: str,
        source_boost: float,
    ) -> DiscoveredContact:
        """
        Classify an email's contact_type and assign a confidence score
        based on prefix pattern matching and source context.
        """
        contact_type = "general"
        base_score = 0.50

        for pattern, ctype, score in cls.CONTACT_PATTERNS:
            if pattern.search(email):
                contact_type = ctype
                base_score = score
                break

        # Apply source boost (capped at 1.0)
        final_score = min(base_score + source_boost, 1.0)

        return DiscoveredContact(
            email=email,
            contact_type=contact_type,
            source=source,
            confidence_score=round(final_score, 2),
        )

    @classmethod
    async def _persist_contacts(
        cls,
        db: AsyncSession,
        company_id: int,
        contacts: List[DiscoveredContact],
    ):
        """
        Store discovered contacts in the database, deduplicating against
        existing records for the same company.
        """
        for contact in contacts:
            # Check if this email already exists for this company
            existing = await db.execute(
                select(CompanyContact).where(
                    CompanyContact.company_id == company_id,
                    CompanyContact.email == contact.email,
                )
            )
            if existing.scalars().first():
                logger.debug(f"Contact already exists: {contact.email}")
                continue

            db_contact = CompanyContact(
                company_id=company_id,
                email=contact.email,
                contact_type=contact.contact_type,
                source=contact.source,
                confidence_score=contact.confidence_score,
                name=getattr(contact, "name", None),
                role=getattr(contact, "role", None),
            )
            db.add(db_contact)

        try:
            await db.commit()
            logger.info(f"Persisted {len(contacts)} contacts for company_id={company_id}")
        except Exception as e:
            logger.error(f"Failed to persist contacts: {e}")
            await db.rollback()

    @classmethod
    async def get_contacts_for_company(
        cls,
        db: AsyncSession,
        company_id: int,
    ) -> List[CompanyContact]:
        """Retrieve all stored contacts for a company, ordered by confidence."""
        result = await db.execute(
            select(CompanyContact)
            .where(CompanyContact.company_id == company_id)
            .order_by(CompanyContact.confidence_score.desc())
        )
        return list(result.scalars().all())
