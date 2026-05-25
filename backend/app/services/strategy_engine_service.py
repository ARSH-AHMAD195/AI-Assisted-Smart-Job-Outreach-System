"""
Strategy Engine Service — data-driven adaptive strategy selection.

Replaces manual/random strategy selection with a recommendation engine
that predicts the best outreach style for a given context.

Uses:
    - Historical engagement data (which styles got opens/replies)
    - Company context (AI startup vs enterprise, industry)
    - Contact type (recruiter, engineering, founder)
    - Role seniority signals from JD parsing
    - Epsilon-greedy exploration (10% experimental picks)

Scoring formula:
    score = (0.4 × historical_performance) +
            (0.3 × context_match) +
            (0.2 × company_type_fit) +
            (0.1 × role_seniority_fit)
"""

import random
import logging
from typing import Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import OutreachQueueItem
from app.models import TrackingEvent
from app.schemas.strategy_recommendation import (
    StrategyRecommendation,
    StrategyPerformance,
    StrategyAlternative,
)

logger = logging.getLogger(__name__)

# --- Context Classifiers ---

COMPANY_TYPE_KEYWORDS = {
    "ai_startup": ["ai", "machine learning", "ml", "deep learning", "llm", "genai", "neural", "data science"],
    "fintech": ["fintech", "banking", "payments", "trading", "blockchain", "crypto", "defi"],
    "saas": ["saas", "platform", "cloud", "subscription", "b2b", "enterprise software"],
    "ecommerce": ["ecommerce", "e-commerce", "marketplace", "retail", "shopping"],
    "healthtech": ["health", "medical", "biotech", "pharma", "clinical", "telemedicine"],
    "devtools": ["developer tools", "devtools", "sdk", "api", "infrastructure", "devops"],
}

ROLE_SENIORITY_KEYWORDS = {
    "senior": ["senior", "lead", "principal", "staff", "architect", "head of", "director"],
    "mid": ["mid", "intermediate", "ii", "iii", "engineer 2", "engineer 3"],
    "junior": ["junior", "entry", "associate", "intern", "trainee", "graduate", "fresher"],
}

# Default strategy fit matrix: company_type → preferred strategies
COMPANY_STRATEGY_FIT: Dict[str, List[str]] = {
    "ai_startup":  ["technical_project", "vision_oriented"],
    "fintech":     ["structured_professional", "concise_role_focused"],
    "saas":        ["balanced_professional", "technical_project"],
    "ecommerce":   ["concise_role_focused", "balanced_professional"],
    "healthtech":  ["structured_professional", "balanced_professional"],
    "devtools":    ["technical_project", "vision_oriented"],
    "enterprise":  ["structured_professional", "concise_role_focused"],
    "unknown":     ["balanced_professional", "concise_role_focused"],
}

# Contact type → preferred strategies
CONTACT_STRATEGY_FIT: Dict[str, str] = {
    "recruiter":   "concise_role_focused",
    "recruiting":  "concise_role_focused",
    "engineering": "technical_project",
    "founder":     "vision_oriented",
    "hr":          "structured_professional",
    "careers":     "balanced_professional",
    "general":     "balanced_professional",
}

ALL_STRATEGIES = [
    "concise_role_focused",
    "technical_project",
    "vision_oriented",
    "structured_professional",
    "balanced_professional",
]

# Exploration rate — 10% experimental picks
EPSILON = 0.10


class StrategyEngineService:
    """Data-driven adaptive strategy recommendation engine."""

    @classmethod
    async def recommend(
        cls,
        db: AsyncSession,
        contact_type: str,
        company_name: Optional[str] = None,
        company_intel: Optional[Dict] = None,
        jd_text: Optional[str] = None,
    ) -> StrategyRecommendation:
        """
        Recommend the best outreach strategy for a given context.

        Args:
            db: Database session
            contact_type: Type of contact (recruiter, engineering, etc.)
            company_name: Optional company name
            company_intel: Optional dict with vision, products, tech_stack
            jd_text: Optional job description for seniority detection

        Returns:
            StrategyRecommendation with confidence, reasoning, and alternatives
        """
        # 1. Classify context
        company_type = cls._classify_company_type(company_intel)
        role_level = cls._detect_role_seniority(jd_text) if jd_text else "mid"

        context_factors = {
            "company_type": company_type,
            "contact_type": contact_type,
            "role_level": role_level,
            "company_name": company_name or "unknown",
        }

        # 2. Get historical performance
        historical = await cls._get_strategy_performance(db)

        # 3. Score each strategy
        scored = cls._score_strategies(
            contact_type=contact_type,
            company_type=company_type,
            role_level=role_level,
            historical=historical,
        )

        # Sort by score descending
        ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
        best_strategy = ranked[0][0]
        best_score = ranked[0][1]

        # 4. Epsilon-greedy exploration
        is_exploration = False
        if random.random() < EPSILON:
            # Pick a random strategy that ISN'T the best
            alternatives = [s for s, _ in ranked[1:]]
            if alternatives:
                best_strategy = random.choice(alternatives)
                best_score = scored[best_strategy]
                is_exploration = True
                logger.info(f"Exploration pick: {best_strategy} (instead of {ranked[0][0]})")

        # 5. Build reasoning
        reasoning = cls._build_reasoning(
            best_strategy, contact_type, company_type, role_level,
            historical, is_exploration,
        )

        # 6. Build alternatives
        alternatives = [
            StrategyAlternative(
                style=style,
                score=round(score, 2),
                reason=cls._strategy_reason(style, contact_type, company_type),
            )
            for style, score in ranked[1:4]  # Top 3 alternatives
        ]

        # 7. Historical performance for recommended strategy
        hist_perf = None
        if best_strategy in historical:
            h = historical[best_strategy]
            hist_perf = StrategyPerformance(
                style=best_strategy,
                sent=h.get("sent", 0),
                opened=h.get("opened", 0),
                replied=h.get("replied", 0),
                open_rate=h.get("open_rate", 0.0),
                reply_rate=h.get("reply_rate", 0.0),
                best_for=h.get("best_for", []),
            )

        return StrategyRecommendation(
            recommended_strategy=best_strategy,
            confidence=round(min(best_score, 1.0), 2),
            reasoning=reasoning,
            context_factors=context_factors,
            alternatives=alternatives,
            historical_performance=hist_perf,
            is_exploration=is_exploration,
        )

    @classmethod
    def _classify_company_type(cls, company_intel: Optional[Dict]) -> str:
        """Classify company type from intel keywords."""
        if not company_intel:
            return "unknown"

        # Combine all intel text
        text = " ".join([
            str(company_intel.get("vision", "")),
            " ".join(company_intel.get("products", [])),
            " ".join(company_intel.get("tech_stack", [])),
            str(company_intel.get("engineering_culture", "")),
        ]).lower()

        best_type = "unknown"
        best_count = 0

        for ctype, keywords in COMPANY_TYPE_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > best_count:
                best_count = count
                best_type = ctype

        return best_type

    @classmethod
    def _detect_role_seniority(cls, jd_text: str) -> str:
        """Detect role seniority from JD text."""
        text_lower = jd_text.lower()

        for level, keywords in ROLE_SENIORITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return level

        return "mid"  # Default

    @classmethod
    async def _get_strategy_performance(cls, db: AsyncSession) -> Dict[str, Dict]:
        """
        Query historical strategy performance from sent queue items
        cross-referenced with tracking events.
        """
        performance: Dict[str, Dict] = {}

        for strategy in ALL_STRATEGIES:
            # Count sent items with this strategy
            sent_result = await db.execute(
                select(func.count(OutreachQueueItem.id))
                .where(
                    OutreachQueueItem.outreach_style == strategy,
                    OutreachQueueItem.status == "sent",
                )
            )
            sent_count = sent_result.scalar() or 0

            if sent_count == 0:
                performance[strategy] = {
                    "sent": 0, "opened": 0, "replied": 0,
                    "open_rate": 0.0, "reply_rate": 0.0, "best_for": [],
                }
                continue

            # Get tracking IDs for this strategy
            ids_result = await db.execute(
                select(OutreachQueueItem.transactional_id)
                .where(
                    OutreachQueueItem.outreach_style == strategy,
                    OutreachQueueItem.status == "sent",
                    OutreachQueueItem.transactional_id.isnot(None),
                )
            )
            tracking_ids = [r[0] for r in ids_result.all() if r[0]]

            opened = 0
            replied = 0

            if tracking_ids:
                open_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type == "OPEN",
                    )
                )
                opened = open_result.scalar() or 0

                reply_result = await db.execute(
                    select(func.count(TrackingEvent.id))
                    .where(
                        TrackingEvent.transactional_id.in_(tracking_ids),
                        TrackingEvent.event_type == "REPLY",
                    )
                )
                replied = reply_result.scalar() or 0

            performance[strategy] = {
                "sent": sent_count,
                "opened": opened,
                "replied": replied,
                "open_rate": round(opened / sent_count, 2) if sent_count > 0 else 0.0,
                "reply_rate": round(replied / sent_count, 2) if sent_count > 0 else 0.0,
                "best_for": [],  # Populated by Phase 4 adaptive optimizer
            }

        return performance

    @classmethod
    def _score_strategies(
        cls,
        contact_type: str,
        company_type: str,
        role_level: str,
        historical: Dict[str, Dict],
    ) -> Dict[str, float]:
        """
        Score each strategy using weighted factors:
            0.4 × historical_performance (reply_rate)
            0.3 × context_match (contact_type fit)
            0.2 × company_type_fit
            0.1 × role_seniority_fit
        """
        scores: Dict[str, float] = {}

        # Get best contact-type strategy
        contact_preferred = CONTACT_STRATEGY_FIT.get(contact_type, "balanced_professional")

        # Get company-type preferred strategies
        company_preferred = COMPANY_STRATEGY_FIT.get(company_type, ["balanced_professional"])

        for strategy in ALL_STRATEGIES:
            # Historical performance (reply_rate as proxy, 0.0–1.0)
            hist = historical.get(strategy, {})
            hist_score = hist.get("reply_rate", 0.0)
            # If no data, give a neutral score so new strategies aren't penalized
            if hist.get("sent", 0) == 0:
                hist_score = 0.15  # Neutral prior

            # Context match — does contact type align?
            context_score = 1.0 if strategy == contact_preferred else 0.3

            # Company type fit
            company_score = 1.0 if strategy in company_preferred else 0.3
            if strategy == company_preferred[0] if company_preferred else False:
                company_score = 1.0  # Top choice gets full score

            # Role seniority fit
            seniority_score = 0.5  # Default neutral
            if role_level == "senior" and strategy in ["technical_project", "vision_oriented"]:
                seniority_score = 1.0
            elif role_level == "junior" and strategy in ["concise_role_focused", "balanced_professional"]:
                seniority_score = 1.0
            elif role_level == "mid":
                seniority_score = 0.7  # Mid-level is flexible

            # Weighted combination
            score = (
                0.4 * hist_score +
                0.3 * context_score +
                0.2 * company_score +
                0.1 * seniority_score
            )
            scores[strategy] = score

        return scores

    @classmethod
    def _build_reasoning(
        cls,
        strategy: str,
        contact_type: str,
        company_type: str,
        role_level: str,
        historical: Dict[str, Dict],
        is_exploration: bool,
    ) -> List[str]:
        """Build human-readable reasoning for the recommendation."""
        reasons = []

        if is_exploration:
            reasons.append("EXPLORATION: Trying a less-used strategy to discover new patterns")

        # Contact type reasoning
        preferred = CONTACT_STRATEGY_FIT.get(contact_type, "balanced_professional")
        if strategy == preferred:
            reasons.append(f"'{strategy}' is the best-performing style for {contact_type} contacts")
        else:
            reasons.append(f"Selected '{strategy}' over typical '{preferred}' for {contact_type} contacts")

        # Company type reasoning
        company_preferred = COMPANY_STRATEGY_FIT.get(company_type, ["balanced_professional"])
        if strategy in company_preferred:
            reasons.append(f"Matches {company_type} company profile (preferred: {', '.join(company_preferred)})")

        # Historical reasoning
        hist = historical.get(strategy, {})
        if hist.get("sent", 0) > 0:
            reasons.append(
                f"Historical: {hist.get('reply_rate', 0)*100:.0f}% reply rate "
                f"across {hist['sent']} sends"
            )
        else:
            reasons.append("No historical data yet — using context-based recommendation")

        # Seniority reasoning
        if role_level == "senior":
            reasons.append(f"Senior-level role — {strategy} appropriate for experienced candidates")
        elif role_level == "junior":
            reasons.append(f"Entry-level role — {strategy} keeps tone accessible")

        return reasons

    @classmethod
    def _strategy_reason(cls, strategy: str, contact_type: str, company_type: str) -> str:
        """Brief reason string for an alternative strategy."""
        reasons = {
            "concise_role_focused": "Direct and skills-focused, best for busy recruiters",
            "technical_project": "References technical work, best for engineering teams",
            "vision_oriented": "Mission-driven, best for founders and startups",
            "structured_professional": "Warm and process-aware, best for HR",
            "balanced_professional": "Well-rounded general approach",
        }
        return reasons.get(strategy, "Alternative approach")
