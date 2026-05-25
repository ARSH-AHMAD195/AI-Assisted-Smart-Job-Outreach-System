"""
Match Explainer Service — AI-powered explainable match analysis.

Transforms raw keyword intersection scores into evidence-backed explanations.
Tells the user WHY they fit, WHAT to emphasize, and WHICH strategy to use.

Flow:
    1. Run existing calculate_match() for raw scoring
    2. Map matched/missing skills to user's projects + experience
    3. Feed everything into an AI prompt for structured explanation
    4. Return MatchExplanation with strategy reasoning

This is the EXPLAINABILITY layer — what makes the system feel intelligent
instead of automated.
"""

import json
import logging
from typing import Dict, List, Optional

from app.schemas.user import FinalUserProfile
from app.schemas.match_explanation import (
    MatchExplanation,
    SkillAlignment,
    GapMitigation,
)
from app.services.job_service import calculate_match
from app.utils.ai_handler import AIHandler

logger = logging.getLogger(__name__)


class MatchExplainerService:
    """Produces explainable, evidence-backed match analyses."""

    @classmethod
    async def explain_match(
        cls,
        user_profile: FinalUserProfile,
        jd_text: str,
        company_intel: Optional[Dict] = None,
        company_name: Optional[str] = None,
    ) -> MatchExplanation:
        """
        Generate an explainable match result.

        Args:
            user_profile: Candidate profile (skills, projects, experience)
            jd_text: Job description text
            company_intel: Optional dict with vision, products, tech_stack, engineering_culture
            company_name: Optional company name for context

        Returns:
            MatchExplanation with evidence-backed analysis + strategy recommendation
        """
        # 1. Run raw keyword matching
        raw_result = calculate_match(user_profile, jd_text)

        # 2. Run semantic matching (Gemini embeddings)
        semantic_result = None
        semantic_score = None
        try:
            from app.services.embedding_service import EmbeddingService
            semantic_result = await EmbeddingService.semantic_match(user_profile, jd_text)
            semantic_score = semantic_result.get("semantic_score")
        except Exception as e:
            logger.warning(f"Semantic matching unavailable, using keyword-only: {e}")

        # 3. Blend scores
        if semantic_score is not None:
            from app.services.embedding_service import EmbeddingService as ES
            combined_score = ES.blend_scores(raw_result.match_score, semantic_score)
        else:
            combined_score = raw_result.match_score

        # Update match label based on combined score
        if combined_score >= 80:
            combined_label = "Excellent"
        elif combined_score >= 50:
            combined_label = "Good"
        else:
            combined_label = "Poor"

        # 4. Build evidence map — connect skills to user's projects/experience
        evidence_map = cls._build_evidence_map(user_profile)

        # 5. Build structured skill alignments
        skill_alignments = cls._build_skill_alignments(
            raw_result.matched_skills,
            raw_result.missing_skills,
            evidence_map,
        )

        # 6. AI-powered explanation + strategy reasoning
        ai_explanation = await cls._generate_ai_explanation(
            user_profile=user_profile,
            jd_text=jd_text,
            raw_result=raw_result,
            evidence_map=evidence_map,
            company_intel=company_intel,
            company_name=company_name,
        )

        # 7. Assemble the MatchExplanation
        return MatchExplanation(
            keyword_score=raw_result.match_score,
            semantic_score=semantic_score,
            combined_score=combined_score,
            match_label=combined_label,
            summary=ai_explanation.get("summary", raw_result.analysis),
            strengths=ai_explanation.get("strengths", []),
            gaps=cls._build_gap_mitigations(
                raw_result.missing_skills,
                ai_explanation.get("gap_mitigations", []),
            ),
            skill_alignments=skill_alignments,
            recommended_strategy=ai_explanation.get("recommended_strategy", "balanced_professional"),
            strategy_reasoning=ai_explanation.get("strategy_reasoning", []),
            emphasis_points=ai_explanation.get("emphasis_points", []),
            company_context_notes=ai_explanation.get("company_context_notes", []),
        )

    @classmethod
    def _build_evidence_map(cls, profile: FinalUserProfile) -> Dict[str, List[str]]:
        """
        Map each user skill to the projects/experiences where it appears.

        Returns:
            { "Python": ["Used in FastAPI project at XYZ", "3yr experience at ABC"], ... }
        """
        evidence: Dict[str, List[str]] = {}

        # From projects
        for proj in profile.projects:
            for tech in proj.tech_stack:
                tech_title = tech.strip().title()
                if tech_title not in evidence:
                    evidence[tech_title] = []
                desc = proj.description[0][:80] if proj.description else "project work"
                evidence[tech_title].append(
                    f"Used in project '{proj.title}' ({desc})"
                )

        # From experience
        for exp in profile.experience:
            for tech in exp.tech_stack:
                tech_title = tech.strip().title()
                if tech_title not in evidence:
                    evidence[tech_title] = []
                evidence[tech_title].append(
                    f"Applied at {exp.organization} as {exp.title} ({exp.duration})"
                )

        # From skills list (generic evidence)
        for skill in profile.skills:
            skill_title = skill.strip().title()
            if skill_title not in evidence:
                evidence[skill_title] = [f"Listed as a core skill"]

        return evidence

    @classmethod
    def _build_skill_alignments(
        cls,
        matched_skills: List[str],
        missing_skills: List[str],
        evidence_map: Dict[str, List[str]],
    ) -> List[SkillAlignment]:
        """Build per-skill alignment records with evidence."""
        alignments = []

        for skill in matched_skills:
            evidence_list = evidence_map.get(skill.title(), [])
            alignments.append(SkillAlignment(
                skill=skill,
                category="mandatory",  # Simplified — JD section parsing handles this
                matched=True,
                user_evidence=evidence_list[0] if evidence_list else None,
                relevance_note="Directly matches JD requirement",
            ))

        for skill in missing_skills:
            alignments.append(SkillAlignment(
                skill=skill,
                category="mandatory",
                matched=False,
                user_evidence=None,
                relevance_note="Required in JD but not found in profile",
            ))

        return alignments

    @classmethod
    def _build_gap_mitigations(
        cls,
        missing_skills: List[str],
        ai_mitigations: List[Dict],
    ) -> List[GapMitigation]:
        """Build gap records with AI-suggested mitigations."""
        gaps = []

        # Index AI mitigations by skill name
        ai_map = {}
        for m in ai_mitigations:
            if isinstance(m, dict) and "skill" in m:
                ai_map[m["skill"].lower()] = m

        for skill in missing_skills:
            ai_data = ai_map.get(skill.lower(), {})
            gaps.append(GapMitigation(
                skill=skill,
                category=ai_data.get("category", "mandatory"),
                severity=ai_data.get("severity", "moderate"),
                mitigation=ai_data.get(
                    "mitigation",
                    f"Mention transferable skills or willingness to learn {skill}"
                ),
            ))

        return gaps

    @classmethod
    async def _generate_ai_explanation(
        cls,
        user_profile: FinalUserProfile,
        jd_text: str,
        raw_result,
        evidence_map: Dict[str, List[str]],
        company_intel: Optional[Dict],
        company_name: Optional[str],
    ) -> Dict:
        """
        Use AIHandler to generate the explainable analysis:
        - Summary (human-readable why-you-fit)
        - Strengths (top reasons to highlight)
        - Gap mitigations (how to address missing skills)
        - Strategy recommendation (which outreach style + why)
        - Emphasis points (what to specifically mention)
        """
        # Build context strings
        skills_str = ", ".join(user_profile.skills[:20])
        projects_str = "\n".join([
            f"- {p.title}: {p.description[0][:100] if p.description else 'N/A'} "
            f"(Tech: {', '.join(p.tech_stack[:5])})"
            for p in user_profile.projects[:5]
        ])
        experience_str = "\n".join([
            f"- {e.title} at {e.organization} ({e.duration})"
            for e in user_profile.experience[:5]
        ])

        matched_str = ", ".join(raw_result.matched_skills[:15])
        missing_str = ", ".join(raw_result.missing_skills[:10])

        # Evidence highlights
        evidence_highlights = []
        for skill in raw_result.matched_skills[:8]:
            evs = evidence_map.get(skill.title(), [])
            if evs:
                evidence_highlights.append(f"{skill}: {evs[0]}")

        intel_context = "No company intelligence available."
        if company_intel:
            parts = []
            if company_intel.get("vision"):
                parts.append(f"Vision: {company_intel['vision']}")
            if company_intel.get("products"):
                parts.append(f"Products: {', '.join(company_intel['products'][:5])}")
            if company_intel.get("tech_stack"):
                parts.append(f"Tech Stack: {', '.join(company_intel['tech_stack'][:8])}")
            if company_intel.get("engineering_culture"):
                parts.append(f"Culture: {company_intel['engineering_culture']}")
            if parts:
                intel_context = "\n".join(parts)

        system_prompt = (
            "You are a Career Intelligence Analyst. Your role is to produce "
            "insightful, evidence-backed match explanations that help a candidate "
            "understand their fit and craft the most effective outreach."
        )

        prompt = f"""
Analyze this candidate-job match and produce a structured explanation.

MATCH SCORE: {raw_result.match_score}% ({raw_result.match_label})
MATCHED SKILLS: {matched_str}
MISSING SKILLS: {missing_str}

CANDIDATE SKILLS: {skills_str}
CANDIDATE PROJECTS:
{projects_str}
CANDIDATE EXPERIENCE:
{experience_str}

EVIDENCE (skill → where used):
{chr(10).join(evidence_highlights) if evidence_highlights else "No specific evidence mapped"}

COMPANY: {company_name or "Unknown"}
COMPANY INTELLIGENCE:
{intel_context}

JOB DESCRIPTION (truncated):
{jd_text[:2500]}

AVAILABLE OUTREACH STRATEGIES:
- concise_role_focused: Best for recruiters, direct and skills-focused
- technical_project: Best for engineering teams, references technical work
- vision_oriented: Best for founders/startups, connects to company mission
- structured_professional: Best for HR, warm and process-aware
- balanced_professional: General purpose, well-researched

OUTPUT FORMAT (JSON ONLY, no markdown):
{{
    "summary": "2-3 sentence human-readable explanation of match quality",
    "strengths": ["Top strength 1", "Top strength 2", "Top strength 3"],
    "gap_mitigations": [
        {{
            "skill": "Missing Skill",
            "category": "mandatory|preferred",
            "severity": "critical|moderate|minor",
            "mitigation": "How to address in outreach"
        }}
    ],
    "recommended_strategy": "strategy_name",
    "strategy_reasoning": ["Reason 1", "Reason 2", "Reason 3"],
    "emphasis_points": ["What to specifically highlight in email 1", "Point 2"],
    "company_context_notes": ["How company intel influenced analysis"]
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

            return json.loads(result_text)

        except Exception as e:
            logger.error(f"AI explanation generation failed: {e}")
            # Fallback to rule-based explanation
            return cls._fallback_explanation(raw_result, company_name)

    @classmethod
    def _fallback_explanation(cls, raw_result, company_name: Optional[str]) -> Dict:
        """Rule-based fallback when AI generation fails."""
        strengths = []
        if len(raw_result.matched_skills) >= 5:
            strengths.append(f"Strong skill overlap: {len(raw_result.matched_skills)} matched skills")
        if raw_result.match_score >= 70:
            strengths.append("High overall match score indicates strong fit")

        strategy = "balanced_professional"
        reasoning = ["Default strategy selected (AI analysis unavailable)"]

        if raw_result.match_score >= 80:
            strategy = "concise_role_focused"
            reasoning = ["High match score — lead with direct role alignment"]
        elif raw_result.match_score >= 50:
            strategy = "technical_project"
            reasoning = ["Moderate match — emphasize project work to demonstrate capability"]

        return {
            "summary": (
                f"Match score of {raw_result.match_score}% ({raw_result.match_label}). "
                f"Matched {len(raw_result.matched_skills)} skills, "
                f"missing {len(raw_result.missing_skills)} skills."
            ),
            "strengths": strengths,
            "gap_mitigations": [
                {"skill": s, "category": "mandatory", "severity": "moderate",
                 "mitigation": f"Highlight transferable experience for {s}"}
                for s in raw_result.missing_skills[:5]
            ],
            "recommended_strategy": strategy,
            "strategy_reasoning": reasoning,
            "emphasis_points": [f"Highlight: {s}" for s in raw_result.matched_skills[:3]],
            "company_context_notes": [
                f"Target company: {company_name}" if company_name else "No company intel available"
            ],
        }
