import os
import smtplib
from email.message import EmailMessage
from app.schemas.email import EmailSendRequest
from dotenv import load_dotenv

load_dotenv()

class SMTPService:
    @staticmethod
    def send_email(request: EmailSendRequest):
        """
        Sends an email using the GMass SMTP Relay.
        Prioritizes .env variables for GMass configuration.
        """
        # GMass SMTP Configuration (Fallbacks to standard GMass defaults)
        SMTP_SERVER = os.getenv("GMASS_HOST", "smtp.gmass.co")
        SMTP_PORT = int(os.getenv("GMASS_PORT", 587))
        
        # GMass Relay logic: Username is always "gmass", Password is the API Key
        SMTP_USER = "gmass"
        
        # Resolve credentials (Priority: .env > Request)
        sender_email = os.getenv("GMASS_EMAIL") or request.sender_email
        api_key = os.getenv("GMASS_API_KEY") or request.app_password

        if not sender_email or not api_key:
            raise Exception("SMTP Configuration Error: Missing sender email or API key (GMASS_API_KEY).")

        # Construct the email
        msg = EmailMessage()
        msg.set_content(request.body)
        msg['Subject'] = request.subject
        msg['From'] = sender_email
        msg['To'] = request.recipient_email

        try:
            # Connect and send via GMass Relay
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()  # Secure the connection
                server.login(SMTP_USER, api_key)
                server.send_message(msg)
            
            return {
                "status": "success", 
                "message": "Email successfully sent via GMass Relay!",
                "sender": sender_email
            }
        except Exception as e:
            raise Exception(f"Failed to send email via GMass: {str(e)}")
