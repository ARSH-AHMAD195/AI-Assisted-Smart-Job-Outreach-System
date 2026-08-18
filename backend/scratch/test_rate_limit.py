import os
import sys
import asyncio
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import AsyncSessionLocal
from app.models.campaign import Campaign, OutreachQueueItem
from app.services.outreach_queue_service import OutreachQueueService

async def run_test():
    db = AsyncSessionLocal()
    campaign_name = "Rate Limit Test Campaign"
    
    try:
        # 1. Reset any prior test campaigns
        res = await db.execute(
            OutreachQueueItem.__table__.delete().where(
                OutreachQueueItem.subject == "Test Email"
            )
        )
        await db.execute(
            Campaign.__table__.delete().where(
                Campaign.name == campaign_name
            )
        )
        await db.commit()

        # 2. Create a test campaign with rate limit of 3 emails/hour
        campaign = Campaign(
            name=campaign_name,
            status="active",
            max_emails_per_hour=3
        )
        db.add(campaign)
        await db.flush()
        print(f"Created test campaign (ID: {campaign.id}) with max_emails_per_hour = 3")

        # 3. Check rate limit initially (should be True)
        can_send = await OutreachQueueService._check_rate_limit(db, campaign)
        print(f"Initial check: can send? {can_send}")

        # 4. Insert 3 sent items to trigger the limit
        for i in range(3):
            item = OutreachQueueItem(
                campaign_id=campaign.id,
                recipient_email=f"test{i}@example.com",
                subject="Test Email",
                status="sent",
                sent_at=datetime.utcnow()
            )
            db.add(item)
        await db.commit()
        print("Inserted 3 'sent' outreach items within the last hour.")

        # 5. Check rate limit again (should be False)
        can_send_full = await OutreachQueueService._check_rate_limit(db, campaign)
        print(f"Check after 3 sends: can send? {can_send_full} (False = Rate limited)")

        # 6. Delete 1 sent item to go below limit
        delete_res = await db.execute(
            OutreachQueueItem.__table__.delete().where(
                OutreachQueueItem.recipient_email == "test0@example.com"
            )
        )
        await db.commit()
        print("Removed 1 sent item.")

        # 7. Check rate limit again (should be True)
        can_send_after_removal = await OutreachQueueService._check_rate_limit(db, campaign)
        print(f"Check after removal: can send? {can_send_after_removal} (True = Within limit)")

    except Exception as e:
        print(f"Test failed with error: {e}")
        await db.rollback()
    finally:
        # Cleanup
        await db.execute(
            OutreachQueueItem.__table__.delete().where(
                OutreachQueueItem.campaign_id == campaign.id
            )
        )
        await db.execute(
            Campaign.__table__.delete().where(
                Campaign.id == campaign.id
            )
        )
        await db.commit()
        await db.close()
        print("Cleanup completed.")

if __name__ == "__main__":
    asyncio.run(run_test())
