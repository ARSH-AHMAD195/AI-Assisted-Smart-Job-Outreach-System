"""
Pydantic schemas for explainable match results.

Moves beyond raw scores to provide evidence-backed skill alignments,
strategy reasoning, and actionable emphasis points for outreach.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class SkillAlignment(BaseModel):
    """A single skill alignment with evidence from the user's profile."""
    skill: str
    category: str = Field(description="mandatory | preferred")
    matched: bool
    user_evidence: Optional[str] = Field(
        default=None,
        description="Where in the user's profile this skill appears (project, experience, etc.)"
    )
    relevance_note: str = Field(
        default="",
        description="Why this skill matters for this role"
    )


class GapMitigation(BaseModel):
    """A missing skill with a suggested mitigation strategy."""
    skill: str
    category: str  # mandatory | preferred
    severity: str  # critical | moderate | minor
    mitigation: str  # Suggested way to address the gap in outreach


class MatchExplanation(BaseModel):
    """
    Explainable match result — tells the user WHY they fit,
    WHAT to emphasize, and WHICH strategy to use.
    """
    # --- Scoring ---
    keyword_score: float = Field(ge=0, le=100, description="Weighted keyword intersection score")
    semantic_score: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Embedding cosine similarity score (Phase 5)"
    )
    combined_score: float = Field(ge=0, le=100, description="Blended final score")
    match_label: str  # Excellent / Good / Poor

    # --- Explainability ---
    summary: str = Field(description="Human-readable 2-3 sentence match explanation")
    strengths: List[str] = Field(
        default_factory=list,
        description="Top reasons to highlight in outreach"
    )
    gaps: List[GapMitigation] = Field(
        default_factory=list,
        description="Missing skills with severity and mitigation suggestions"
    )
    skill_alignments: List[SkillAlignment] = Field(
        default_factory=list,
        description="Per-skill breakdown with evidence"
    )

    # --- Strategy Guidance ---
    recommended_strategy: str = Field(
        description="Which outreach style to use (technical_project, vision_oriented, etc.)"
    )
    strategy_reasoning: List[str] = Field(
        default_factory=list,
        description="WHY this strategy was chosen"
    )
    emphasis_points: List[str] = Field(
        default_factory=list,
        description="What to specifically highlight in the email"
    )
    company_context_notes: List[str] = Field(
        default_factory=list,
        description="How company intelligence informed the analysis"
    )
