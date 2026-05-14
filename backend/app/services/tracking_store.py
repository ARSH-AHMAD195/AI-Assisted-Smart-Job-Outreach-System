"""
In-memory + JSON-file-backed store for email tracking events.

Stores webhook events (opens, replies, bounces, clicks) received from GMass,
keyed by recipient email. Persists to tracking_data.json for durability
across server restarts.

NOTE: This is a simple file-based store for MVP/development.
Replace with a database (SQLite/PostgreSQL) when scaling.
"""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional


DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tracking_data.json")


class TrackingStore:
    """Singleton store for email tracking events."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._events = []  # List of all tracking events
        self._load()

    def _load(self):
        """Load persisted events from JSON file."""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    self._events = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._events = []

    def _save(self):
        """Persist events to JSON file."""
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self._events, f, indent=2, default=str)
        except IOError as e:
            print(f"Warning: Failed to save tracking data: {e}")

    def add_event(self, event: dict):
        """Add a tracking event and persist."""
        event.setdefault("received_at", datetime.now(timezone.utc).isoformat())
        self._events.append(event)
        self._save()

    def get_events_for_email(self, email: str) -> list:
        """Get all events for a specific recipient email."""
        return [
            e for e in self._events
            if e.get("email_address", "").lower() == email.lower()
        ]

    def get_events_by_type(self, event_type: str) -> list:
        """Get all events of a specific type (opens, replies, bounces, clicks)."""
        return [
            e for e in self._events
            if e.get("event_type", "").lower() == event_type.lower()
        ]

    def get_events_for_tracking_id(self, tracking_id: str) -> list:
        """Get all events for a specific transactional email ID."""
        return [
            e for e in self._events
            if e.get("tracking_id", "") == tracking_id
        ]

    def get_all_events(self) -> list:
        """Get all stored tracking events."""
        return list(self._events)

    def get_summary(self) -> dict:
        """Get aggregated counts by event type."""
        summary = {"opens": 0, "replies": 0, "bounces": 0, "clicks": 0, "sends": 0}
        for e in self._events:
            etype = e.get("event_type", "").lower()
            if etype in summary:
                summary[etype] += 1
        return summary

    def clear(self):
        """Clear all events (for testing)."""
        self._events = []
        self._save()
