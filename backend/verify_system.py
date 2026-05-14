import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_pipeline():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Test Role Inference
        print("\n--- Testing Role Inference ---")
        profile_mock = {
            "name": "Om Anand",
            "email": "om@example.com",
            "phone": "1234567890",
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "projects": [
                {
                    "title": "Job Outreach System",
                    "description": ["Built an AI-powered system for job outreach using FastAPI and Llama 3."]
                }
            ],
            "experience": [],
            "education": []
        }
        try:
            resp = await client.post(f"{BASE_URL}/api/jobs/infer-roles", json=profile_mock)
            print(f"Inference Response: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
        except Exception as e:
            print(f"Inference failed: {e}")

        # 2. Test Job Discovery
        print("\n--- Testing Job Discovery ---")
        try:
            resp = await client.get(f"{BASE_URL}/api/jobs/discover?role=Backend+Developer")
            print(f"Discovery Response: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
        except Exception as e:
            print(f"Discovery failed: {e}")

        # 3. Test Company Intelligence
        print("\n--- Testing Company Intelligence ---")
        try:
            resp = await client.get(f"{BASE_URL}/api/company/enrich?name=OpenAI&url=https://openai.com")
            print(f"Intelligence Response: {resp.status_code}")
            print(json.dumps(resp.json(), indent=2))
        except Exception as e:
            print(f"Intelligence failed: {e}")

if __name__ == "__main__":
    # Note: Ensure the server is running before running this test
    print("This script requires the FastAPI server to be running on http://localhost:8000")
    # asyncio.run(test_pipeline())
