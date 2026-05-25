"""
Pydantic schemas for the Strategy Recommendation Engine.

Provides structured, explainable strategy recommendations
with confidence scores, context factors, and historical performance data.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class StrategyPerformance(BaseModel):
    """Historical performance metrics for a single strategy."""
    style: str
    sent: int = 0
    opened: int = 0
    replied: int = 0
    open_rate: float = 0.0
    reply_rate: float = 0.0
    best_for: List[str] = Field(
        default_factory=list,
        description="Contexts where this strategy performs best (e.g., 'AI startups', 'backend roles')"
    )


class StrategyAlternative(BaseModel):
    """A ranked alternative strategy."""
    style: str
    score: float = Field(ge=0, le=1.0)
    reason: str


class StrategyRecommendation(BaseModel):
    """
    Data-driven strategy recommendation with full reasoning.

    Produced by the StrategyEngineService using historical engagement
    data + company context to predict best-performing outreach style.
    """
    recommended_strategy: str
    confidence: float = Field(ge=0, le=1.0)
    reasoning: List[str] = Field(
        default_factory=list,
        description="Human-readable reasons for the recommendation"
    )
    context_factors: Dict[str, str] = Field(
        default_factory=dict,
        description="What influenced the choice: company_type, contact_type, role_level, etc."
    )
    alternatives: List[StrategyAlternative] = Field(
        default_factory=list,
        description="Ranked alternatives with scores"
    )
    historical_performance: Optional[StrategyPerformance] = Field(
        default=None,
        description="How the recommended strategy has performed historically"
    )
    is_exploration: bool = Field(
        default=False,
        description="True if this was an epsilon-greedy exploration pick"
    )
