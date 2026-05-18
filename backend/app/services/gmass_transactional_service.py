"""
Async service for sending emails via the GMass Transactional API.

Sends individual tracked emails with open/click tracking enabled.
Wraps plain-text body in HTML for tracking pixel injection.
Uses httpx.AsyncClient with X-apikey header authentication.
"""

import os
from dotenv import load_dotenv
import httpx

load_dotenv()

GMASS_API_URL = "https://api.gmass.co/api/transactional"


class GMassTransactionalService:
    """Sends tracked transactional emails via the GMass API."""

    @staticmethod
    async def send_email(
        recipient_email: str,
        subject: str,
        body: str,
        sender_email: str = None,
        sender_name: str = None,
    ) -> dict:
        """
        Send a single transactional email with open/click tracking.

        Args:
            recipient_email: The recipient's email address.
            subject: Email subject line.
            body: Email body (plain text — will be wrapped in HTML).
            sender_email: Optional sender email override.
            sender_name: Optional sender display name.

        Returns:
            dict with status, message, tracking_id, and sender.
        """
        api_key = os.getenv("GMASS_API_KEY")
        if not api_key:
            raise Exception("GMASS_API_KEY is not set in environment variables.")

        from_email = sender_email or os.getenv("GMASS_EMAIL")
        if not from_email:
            raise Exception("No sender email configured (GMASS_EMAIL).")

        # Wrap body in HTML for tracking pixel injection
        html_body = _wrap_in_html(body)

        payload = {
            "to": recipient_email,
            "subject": subject,
            "message": html_body,
            "settings": {
                "openTrack": True,
                "clickTrack": True,
                "messageType": "html",
            },
            "correlationId": recipient_email, # Link back to our DB via email
        }

        if from_email:
            payload["fromEmail"] = from_email
        if sender_name:
            payload["fromName"] = sender_name

        headers = {
            "X-apikey": api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                GMASS_API_URL,
                json=payload,
                headers=headers,
                timeout=30.0,
            )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(
                f"GMass Transactional API error (HTTP {response.status_code}): {error_text}"
            )

        result = response.json()

        # Extract the transactional email ID for tracking
        tracking_id = result.get("transactionalEmailId", "")

        return {
            "status": "success",
            "message": "Email sent via GMass Transactional API with tracking enabled!",
            "sender": from_email,
            "tracking_id": tracking_id,
            "tracking_enabled": True,
        }


def _wrap_in_html(plain_text: str) -> str:
    """
    Wrap plain text body in HTML tags for GMass tracking pixel injection.

    GMass requires <html><body> tags to insert the 1x1 tracking pixel.
    Preserves line breaks and basic formatting.
    """
    # If body already looks like HTML, return as-is
    if "<html" in plain_text.lower() or "<body" in plain_text.lower():
        return plain_text

    # Convert line breaks to <br> and wrap in HTML
    html_lines = plain_text.replace("\n", "<br>\n")

    return f"""<html>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px; color: #333; line-height: 1.6;">
{html_lines}
</body>
</html>"""
