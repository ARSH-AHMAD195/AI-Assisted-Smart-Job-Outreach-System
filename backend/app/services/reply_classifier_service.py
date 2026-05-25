"""
Reply Classifier Service — AI-powered reply intent classification.

Classifies incoming reply content into actionable intents:
    - positive_interest  → wants to proceed ("Let's schedule a call")
    - request_info       → needs more info ("Can you send your resume?")
    - soft_rejection     → polite decline ("Not hiring right now")
    - hard_rejection     → definitive no ("Please don't contact us again")
    - auto_reply         → OOO, generic autoresponder
    - referral           → redirects to someone else ("Try reaching out to X")

Architecture:
    Webhook detects reply event
        ↓
    (Future: Fetch thread via Gmail API for full content)
        ↓
    Run classification via AIHandler
        ↓
    Emit OutreachEvent + update contact confidence
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outreach_event import OutreachEvent
from app.models.campaign import OutreachQueueItem
from app.models.contact import CompanyContact
from app.utils.ai_handler import AIHandler

logger = logging.getLogger(__name__)


class ReplyClassification(BaseModel):
    """Structured reply classification result."""
    intent: str = Field(description="positive_interest|request_info|soft_rejection|hard_rejection|auto_reply|referral")
    confidence: float = Field(ge=0, le=1.0)
    suggested_action: str = Field(description="schedule_followup|send_resume|stop_outreach|wait_and_retry|discover_referral")
    follow_up_recommended: bool = False
    follow_up_delay_days: Optional[int] = None
    reasoning: str = ""


# Confidence adjustments per intent
INTENT_CONFIDENCE_DELTAS = {
    "positive_interest": +0.15,
    "request_info":      +0.10,
    "soft_rejection":    -0.05,
    "hard_rejection":    -0.20,
    "auto_reply":         0.00,
    "referral":          +0.05,
}

# Suggested actions per intent
INTENT_ACTIONS = {
    "positive_interest": "schedule_followup",
    "request_info":      "send_resume",
    "soft_rejection":    "wait_and_retry",
    "hard_rejection":    "stop_outreach",
    "auto_reply":        "wait_and_retry",
    "referral":          "discover_referral",
}


class ReplyClassifierService:
    """Classifies reply intent and triggers appropriate follow-up actions."""

    @classmethod
    async def classify_reply(
        cls,
        reply_text: str,
        original_subject: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> ReplyClassification:
        """
        Classify a reply using AI analysis.

        Args:
            reply_text: The reply content (or metadata if body unavailable)
            original_subject: Subject line of the original outreach
            recipient_email: Who replied

        Returns:
            ReplyClassification with intent, confidence, and suggested action
        """
        # If reply_text is very short or empty, use metadata-based classification
        if not reply_text or len(reply_text.strip()) < 10:
            return cls._metadata_classification(original_subject, recipient_email)

        system_prompt = (
            "You are an Email Reply Intent Classifier for a job outreach system. "
            "Classify the intent of reply emails accurately and suggest next actions."
        )

        prompt = f"""
Classify the intent of this email reply to a job outreach message.

ORIGINAL SUBJECT: {original_subject or "Unknown"}
REPLY FROM: {recipient_email or "Unknown"}
REPLY CONTENT:
---
{reply_text[:2000]}
---

INTENT CATEGORIES:
- positive_interest: Wants to proceed (scheduling, discussing, interested)
- request_info: Needs more information (resume, portfolio, work samples)
- soft_rejection: Polite decline (not hiring, position filled, timing)
- hard_rejection: Definitive no (do not contact, not interested, spam complaint)
- auto_reply: Out of office, autoresponder, generic acknowledgment
- referral: Redirects to another person or department

OUTPUT FORMAT (JSON ONLY, no markdown):
{{
    "intent": "category_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this classification",
    "follow_up_recommended": true,
    "follow_up_delay_days": 3
}}
"""

        try:
            result_text = await AIHandler.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                provider="auto",
            )

            # Extract JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            data = json.loads(result_text)

            intent = data.get("intent", "auto_reply")
            if intent not in INTENT_ACTIONS:
                intent = "auto_reply"

            return ReplyClassification(
                intent=intent,
                confidence=data.get("confidence", 0.5),
                suggested_action=INTENT_ACTIONS[intent],
                follow_up_recommended=data.get("follow_up_recommended", False),
                follow_up_delay_days=data.get("follow_up_delay_days"),
                reasoning=data.get("reasoning", "AI classification"),
            )

        except Exception as e:
            logger.error(f"Reply classification failed: {e}")
            return cls._metadata_classification(original_subject, recipient_email)

    @classmethod
    def _metadata_classification(
        cls,
        subject: Optional[str],
        email: Optional[str],
    ) -> ReplyClassification:
        """
        Fallback classification when reply body is unavailable.
        Uses subject line patterns and metadata signals.
        """
        intent = "positive_interest"  # Optimistic default — a reply is engagement
        confidence = 0.40  # Low confidence without body text

        if subject:
            subject_lower = subject.lower()
            # Auto-reply patterns
            if any(kw in subject_lower for kw in ["out of office", "ooo", "automatic reply", "auto-reply", "autoreply"]):
                intent = "auto_reply"
                confidence = 0.85
            # Rejection patterns
            elif any(kw in subject_lower for kw in ["not interested", "no thanks", "unsubscribe"]):
                intent = "hard_rejection"
                confidence = 0.70
            # Positive patterns
            elif any(kw in subject_lower for kw in ["re:", "interested", "let's", "schedule", "call"]):
                intent = "positive_interest"
                confidence = 0.55

        return ReplyClassification(
            intent=intent,
            confidence=confidence,
            suggested_action=INTENT_ACTIONS[intent],
            follow_up_recommended=intent in ["positive_interest", "request_info"],
            follow_up_delay_days=3 if intent == "positive_interest" else None,
            reasoning="Metadata-based classification (reply body unavailable)",
        )

    @classmethod
    async def process_reply_event(
        cls,
        db: AsyncSession,
        tracking_id: str,
        reply_text: Optional[str] = None,
        reply_subject: Optional[str] = None,
    ) -> Optional[ReplyClassification]:
        """
        Full reply processing pipeline:
        1. Find the queue item by tracking ID
        2. Classify the reply
        3. Update contact behavioral confidence
        4. Emit an OutreachEvent
        5. Return the classification

        Args:
            db: Database session
            tracking_id: GMass transactional ID
            reply_text: Reply body (may be None if webhook only provides metadata)
            reply_subject: Reply subject line
        """
        # 1. Find the queue item
        result = await db.execute(
            select(OutreachQueueItem).where(
                OutreachQueueItem.transactional_id == tracking_id
            )
        )
        queue_item = result.scalars().first()

        if not queue_item:
            logger.warning(f"No queue item found for tracking_id={tracking_id}")
            return None

        # 2. Classify the reply
        classification = await cls.classify_reply(
            reply_text=reply_text or "",
            original_subject=queue_item.subject,
            recipient_email=queue_item.recipient_email,
        )

        # 3. Update contact behavioral confidence
        if queue_item.contact_id:
            await cls._update_contact_confidence(
                db, queue_item.contact_id, classification.intent
            )

        # 4. Emit OutreachEvent
        event = OutreachEvent(
            event_type="reply_classified",
            entity_type="queue_item",
            entity_id=str(queue_item.id),
            payload={
                "intent": classification.intent,
                "confidence": classification.confidence,
                "suggested_action": classification.suggested_action,
                "reasoning": classification.reasoning,
                "follow_up_recommended": classification.follow_up_recommended,
                "recipient_email": queue_item.recipient_email,
                "outreach_style": queue_item.outreach_style,
                "campaign_id": queue_item.campaign_id,
                "tracking_id": tracking_id,
            },
        )
        db.add(event)

        # 5. If hard rejection, mark contact as blacklisted
        if classification.intent == "hard_rejection" and queue_item.contact_id:
            contact_result = await db.execute(
                select(CompanyContact).where(
                    CompanyContact.id == queue_item.contact_id
                )
            )
            contact = contact_result.scalars().first()
            if contact:
                contact.is_verified = False  # Effectively blacklisted
                contact.confidence_score = max(contact.confidence_score - 0.30, 0.0)

                # Emit blacklist event
                blacklist_event = OutreachEvent(
                    event_type="contact_blacklisted",
                    entity_type="contact",
                    entity_id=str(contact.id),
                    payload={
                        "reason": "Hard rejection received",
                        "email": contact.email,
                        "previous_confidence": contact.confidence_score + 0.30,
                    },
                )
                db.add(blacklist_event)

        # 6. Emit strategy performance event
        if queue_item.outreach_style:
            strategy_event = OutreachEvent(
                event_type="variant_scored",
                entity_type="campaign",
                entity_id=str(queue_item.campaign_id),
                payload={
                    "outreach_style": queue_item.outreach_style,
                    "reply_intent": classification.intent,
                    "is_positive": classification.intent in ["positive_interest", "request_info"],
                    "recipient_type": queue_item.recipient_type,
                },
            )
            db.add(strategy_event)

        await db.commit()

        logger.info(
            f"Reply classified: {queue_item.recipient_email} → "
            f"{classification.intent} ({classification.confidence:.0%})"
        )
        return classification

    @classmethod
    async def _update_contact_confidence(
        cls,
        db: AsyncSession,
        contact_id: int,
        intent: str,
    ):
        """Update contact's behavioral confidence based on reply intent."""
        delta = INTENT_CONFIDENCE_DELTAS.get(intent, 0.0)
        if delta == 0.0:
            return

        result = await db.execute(
            select(CompanyContact).where(CompanyContact.id == contact_id)
        )
        contact = result.scalars().first()
        if contact:
            old_score = contact.confidence_score
            contact.confidence_score = max(0.0, min(1.0, contact.confidence_score + delta))
            logger.debug(
                f"Contact {contact.email}: confidence {old_score:.2f} → "
                f"{contact.confidence_score:.2f} (delta={delta:+.2f}, intent={intent})"
            )
