import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import AsyncSessionLocal
from app.models import OutreachEmail, TrackingEvent, User, JobListing
from sqlalchemy import select, delete

async def run_test():
    client = TestClient(app)
    db = AsyncSessionLocal()
    
    test_tracking_id = "test-reply-tracking-uuid"
    test_email = "candidate-test@example.com"
    
    try:
        print("=== STARTING REPLY TRACKING TEST (TEST CASE 8) ===")
        
        # 1. Clean up any existing records
        await db.execute(delete(TrackingEvent).where(TrackingEvent.transactional_id == test_tracking_id))
        await db.execute(delete(OutreachEmail).where(OutreachEmail.transactional_id == test_tracking_id))
        await db.commit()
        
        # 2. Insert mock user and job if needed
        # We find or insert a dummy user
        user_result = await db.execute(select(User).limit(1))
        dummy_user = user_result.scalars().first()
        user_id = dummy_user.user_id if dummy_user else "dummy-user-id"
        
        if not dummy_user:
            dummy_user = User(user_id=user_id, email="dummy@example.com", password_hash="dummy")
            db.add(dummy_user)
            await db.commit()

        # Find or insert dummy job
        job_result = await db.execute(select(JobListing).limit(1))
        dummy_job = job_result.scalars().first()
        job_id = dummy_job.id if dummy_job else 99999
        
        if not dummy_job:
            dummy_job = JobListing(id=job_id, title="Dummy Job", company_name="Dummy Corp", job_url="http://dummy.url")
            db.add(dummy_job)
            await db.commit()

        # 3. Create mock outreach email in SENT state
        outreach = OutreachEmail(
            transactional_id=test_tracking_id,
            recipient_email=test_email,
            subject="Outreach System Interest",
            body="Hello, I am interested in your open role.",
            strategy="concise_role_focused",
            status="SENT",
            job_id=job_id,
            user_id=user_id
        )
        db.add(outreach)
        await db.commit()
        print(f"Mock email created with status 'SENT' (Tracking ID: {test_tracking_id})")

        # 4. Trigger Webhook Event (Simulate GMass Callback)
        webhook_payload = {
            "CorrelationID": test_tracking_id,
            "Email Address": test_email,
            "EventType": "Replies",
            "Subject": "Re: Outreach System Interest",
            "Body": "Yes, let's schedule a call for next Tuesday at 10 AM.",
            "Timestamp": "2026-06-19T20:41:00Z"
        }
        
        print("Sending reply webhook payload to /api/gmass-webhook...")
        response = client.post("/api/gmass-webhook", json=webhook_payload)
        
        assert response.status_code == 200, f"Webhook failed: {response.text}"
        print(f"Webhook responded successfully: {response.json()}")

        # Refresh database session to fetch updates
        db_check = AsyncSessionLocal()
        
        # 5. Verify status update on OutreachEmail
        email_result = await db_check.execute(
            select(OutreachEmail).where(OutreachEmail.transactional_id == test_tracking_id)
        )
        updated_email = email_result.scalars().first()
        print(f"Updated Email status in DB: '{updated_email.status}'")
        assert updated_email.status == "REPLIED", f"Expected 'REPLIED', got '{updated_email.status}'"
        print("[SUCCESS] OutreachEmail status updated to 'REPLIED'.")

        # 6. Verify TrackingEvent creation
        event_result = await db_check.execute(
            select(TrackingEvent).where(TrackingEvent.transactional_id == test_tracking_id)
        )
        tracking_event = event_result.scalars().first()
        print(f"TrackingEvent created? {tracking_event is not None}")
        assert tracking_event is not None, "Tracking event not found in database"
        assert tracking_event.event_type == "Replies", f"Expected event_type 'Replies', got '{tracking_event.event_type}'"
        print("[SUCCESS] TrackingEvent saved with event_type 'Replies'.")

        print("\n=== TEST RESULT: PASSED ===")

    except Exception as e:
        print(f"\n=== TEST RESULT: FAILED ({e}) ===")
        raise e
    finally:
        # Cleanup
        print("Cleaning up test data...")
        await db.execute(delete(TrackingEvent).where(TrackingEvent.transactional_id == test_tracking_id))
        await db.execute(delete(OutreachEmail).where(OutreachEmail.transactional_id == test_tracking_id))
        await db.commit()
        await db.close()
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(run_test())
