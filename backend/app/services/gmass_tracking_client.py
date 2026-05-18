"""
Async client for polling the GMass REST API for email tracking data.

Provides methods to retrieve campaign opens, replies, summary stats,
and a unified full report. Uses httpx.AsyncClient with the X-apikey header.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import httpx
from fastapi import HTTPException

from app.schemas.tracking import (
    OpenRecord,
    ReplyRecord,
    CampaignSummary,
    CampaignTrackingReport,
)

load_dotenv()

GMASS_BASE_URL = "https://api.gmass.co/api"


class GMassTrackingClient:
    """Reusable async client for GMass campaign tracking endpoints."""

    def __init__(self):
        self.api_key = os.getenv("GMASS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GMASS_API_KEY is not set. "
                "Add it to your .env file or environment variables."
            )
        self.headers = {"X-apikey": self.api_key}

    async def _get(self, path: str) -> dict | list:
        """Send an async GET request to a GMass API path and return parsed JSON."""
        url = f"{GMASS_BASE_URL}{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, timeout=30.0)

        if response.status_code != 200:
            detail = (
                f"GMass API error (HTTP {response.status_code}): "
                f"{response.text}"
            )
            raise HTTPException(status_code=response.status_code, detail=detail)

        return response.json()

    async def get_opens(self, campaign_id: int) -> list[OpenRecord]:
        """Fetch who opened/read the email for a given campaign."""
        data = await self._get(f"/reports/{campaign_id}/opens")

        # Normalize: GMass may return a list of dicts or an object with a list
        records = data if isinstance(data, list) else data.get("opens", [])

        return [
            OpenRecord(
                email=record.get("emailAddress", record.get("email", "")),
                open_count=record.get("openCount", record.get("open_count", 0)),
                last_opened_at=record.get("lastOpenedTime", record.get("last_opened_at")),
            )
            for record in records
        ]

    async def get_replies(self, campaign_id: int) -> list[ReplyRecord]:
        """Fetch who replied to the campaign email."""
        data = await self._get(f"/reports/{campaign_id}/replies")

        records = data if isinstance(data, list) else data.get("replies", [])

        return [
            ReplyRecord(
                email=record.get("emailAddress", record.get("email", "")),
                replied_at=record.get("repliedTime", record.get("replied_at")),
            )
            for record in records
        ]

    async def get_campaign_summary(self, campaign_id: int) -> CampaignSummary:
        """Fetch aggregated campaign stats (opens, replies, bounces)."""
        data = await self._get(f"/campaigns/{campaign_id}")

        return CampaignSummary(
            open_count=data.get("opens", data.get("open_count", 0)),
            reply_count=data.get("replies", data.get("reply_count", 0)),
            bounce_count=data.get("bounces", data.get("bounce_count", 0)),
        )

    async def get_full_report(self, campaign_id: int) -> CampaignTrackingReport:
        """Fetch the unified tracking report by calling all three endpoints."""
        opens = await self.get_opens(campaign_id)
        replies = await self.get_replies(campaign_id)
        summary = await self.get_campaign_summary(campaign_id)

        return CampaignTrackingReport(
            campaign_id=campaign_id,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            summary=summary,
            opens=opens,
            replies=replies,
        )
