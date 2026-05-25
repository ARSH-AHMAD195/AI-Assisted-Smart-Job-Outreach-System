"""
Intelligence Router — REST endpoints for the reasoning and intelligence layer.

This is the API surface that makes the system feel intelligent:
    - Explainable match analysis (WHY you fit + WHAT to emphasize)
    - Strategy recommendations (WHICH approach + WHY it was chosen)
    - Reply classification (manual trigger for debugging)
    - Strategy insights (aggregated performance with context)
    - Optimization report (current system intelligence state)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import FinalUserProfile
from app.schemas.match_explanation import MatchExplanation
from app.schemas.strategy_recommendation import StrategyRecommendation

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])


# --- Request Schemas ---

class ExplainMatchRequest(BaseModel):
    """Request for explainable match analysis."""
    user_profile: FinalUserProfile
    jd_text: str
    company_name: Optional[str] = None
    company_intel: Optional[dict] = None


class RecommendStrategyRequest(BaseModel):
    """Request for strategy recommendation."""
    contact_type: str
    company_name: Optional[str] = None
    company_intel: Optional[dict] = None
    jd_text: Optional[str] = None


class ClassifyReplyRequest(BaseModel):
    """Request for manual reply classification."""
    reply_text: str
    original_subject: Optional[str] = None
    recipient_email: Optional[str] = None


# --- Endpoints ---

@router.post("/explain-match", response_model=MatchExplanation)
async def explain_match(
    payload: ExplainMatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Explainable match analysis — tells the user WHY they fit,
    WHAT to emphasize, and WHICH strategy to use.

    Combines keyword intersection + semantic similarity (Gemini embeddings)
    with AI-powered explanation and strategy reasoning.
    """
    from app.services.match_explainer_service import MatchExplainerService

    try:
        explanation = await MatchExplainerService.explain_match(
            user_profile=payload.user_profile,
            jd_text=payload.jd_text,
            company_intel=payload.company_intel,
            company_name=payload.company_name,
        )
        return explanation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Match explanation failed: {str(e)}"
        )


@router.post("/recommend-strategy", response_model=StrategyRecommendation)
async def recommend_strategy(
    payload: RecommendStrategyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Data-driven strategy recommendation — predicts the best outreach
    style using historical performance + context analysis.

    Uses epsilon-greedy exploration (10% experimental picks) to
    prevent strategy overfitting.
    """
    from app.services.strategy_engine_service import StrategyEngineService

    try:
        recommendation = await StrategyEngineService.recommend(
            db=db,
            contact_type=payload.contact_type,
            company_name=payload.company_name,
            company_intel=payload.company_intel,
            jd_text=payload.jd_text,
        )
        return recommendation
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Strategy recommendation failed: {str(e)}"
        )


@router.post("/classify-reply")
async def classify_reply(
    payload: ClassifyReplyRequest,
):
    """
    Classify reply intent — manual trigger for debugging
    and testing the classification pipeline.

    Categories: positive_interest, request_info, soft_rejection,
    hard_rejection, auto_reply, referral
    """
    from app.services.reply_classifier_service import ReplyClassifierService

    try:
        classification = await ReplyClassifierService.classify_reply(
            reply_text=payload.reply_text,
            original_subject=payload.original_subject,
            recipient_email=payload.recipient_email,
        )
        return classification.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reply classification failed: {str(e)}"
        )


@router.get("/strategy-insights")
async def get_strategy_insights(
    db: AsyncSession = Depends(get_db),
):
    """
    Aggregated strategy performance with contextual breakdowns.

    Shows per-strategy metrics (sent, open_rate, reply_rate)
    broken down by contact type, with "best_for" context.
    """
    from app.services.adaptive_optimizer_service import AdaptiveOptimizerService

    try:
        insights = await AdaptiveOptimizerService.get_strategy_insights(db)
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Strategy insights failed: {str(e)}"
        )


@router.get("/optimization-report")
async def get_optimization_report(
    db: AsyncSession = Depends(get_db),
):
    """
    Current optimization state — behavioral scores, strategy performance,
    reply classification summary, and recent optimization events.
    """
    from app.services.adaptive_optimizer_service import AdaptiveOptimizerService

    try:
        report = await AdaptiveOptimizerService.get_optimization_report(db)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization report failed: {str(e)}"
        )
