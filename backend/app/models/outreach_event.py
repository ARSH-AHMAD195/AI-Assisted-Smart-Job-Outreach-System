"""
OutreachEvent — event-sourced model for the intelligence layer.

Lightweight, schema-flexible event store that decouples the system.
Uses JSON payloads (no foreign keys) for maximum flexibility during
the experimentation phase.

Event types:
    - campaign_created, campaign_started, campaign_completed
    - email_sent, email_opened, email_replied, email_bounced
    - reply_classified (positive_interest, soft_rejection, etc.)
    - strategy_recommended (which strategy + why)
    - variant_scored (strategy performance update)
    - confidence_updated (contact behavioral confidence change)
    - contact_discovered, contact_blacklisted
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, Index,
)

from app.database import Base


class OutreachEvent(Base):
    """
    Event-sourced model for intelligence layer telemetry.

    Keeps payloads as JSON for flexibility — event schemas
    evolve rapidly during the intelligence development phase.
    """
    __tablename__ = "outreach_events"

    id = Column(Integer, primary_key=True, index=True)

    # Event classification
    event_type = Column(String, index=True, nullable=False)

    # Entity reference (flexible — no FK constraints)
    entity_type = Column(String, nullable=True)   # campaign, queue_item, contact, company
    entity_id = Column(String, index=True, nullable=True)

    # Event payload — schema-free JSON
    payload = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Composite index for common query patterns
    __table_args__ = (
        Index("ix_events_type_entity", "event_type", "entity_type", "entity_id"),
        Index("ix_events_type_created", "event_type", "created_at"),
    )

    def __repr__(self):
        return (
            f"<OutreachEvent(id={self.id}, type='{self.event_type}', "
            f"entity={self.entity_type}/{self.entity_id})>"
        )
