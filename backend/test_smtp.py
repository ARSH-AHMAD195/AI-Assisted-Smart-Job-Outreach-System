import sys
import os
from dotenv import load_dotenv

# Ensure the app directory is in the path so we can import from app.services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.smtp_service import SMTPService
from app.schemas.email import EmailSendRequest

def test_smtp_send(recipient_email):
    """
    Standalone test script to verify GMass SMTP configuration.
    """
    load_dotenv()
    
    print(f"🚀 Initiating SMTP Test via GMass Relay...")
    print(f"📡 Host: {os.getenv('GMASS_HOST', 'smtp.gmass.co')}")
    print(f"📧 Sender: {os.getenv('GMASS_EMAIL')}")
    print(f"🎯 Recipient: {recipient_email}")
    print("-" * 40)

    # Prepare a mock request
    # Note: We don't need to pass sender_email/app_password if they are in .env,
    # as the service handles the fallback logic.
    test_request = EmailSendRequest(
        recipient_email=recipient_email,
        subject="Outreach System: SMTP Test Connection",
        body="Hello!\n\nThis is a test email from your AI-Assisted Smart Job Outreach System.\nIf you are reading this, your GMass SMTP Relay is configured correctly.\n\nBest,\nYour Digital Twin"
    )

    try:
        result = SMTPService.send_email(test_request)
        print(f"✅ Success! {result['message']}")
    except Exception as e:
        print(f"❌ Failed! Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_smtp.py <recipient_email>")
        sys.exit(1)
    
    target = sys.argv[1]
    test_smtp_send(target)
