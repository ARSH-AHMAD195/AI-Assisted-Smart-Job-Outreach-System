import asyncio
import logging
import sys
import os

# Add the project root to sys.path to import jobspy and app
sys.path.append(os.getcwd())

from app.services.discovery.jobspy_discovery import JobSpyDiscoveryService

logging.basicConfig(level=logging.INFO)

async def test_discovery():
    print("Testing JobSpy discovery...")
    results = await JobSpyDiscoveryService.discover_and_enrich("Python Developer", "India", limit=2)
    print(f"Found {len(results)} jobs.")
    for res in results:
        print(f"- {res.base_job_listing.title} at {res.base_job_listing.company} ({res.base_job_listing.link})")

if __name__ == "__main__":
    asyncio.run(test_discovery())
