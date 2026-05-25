"""
Embedding Service — Gemini-powered semantic matching.

Uses the text-embedding-004 model for cosine similarity scoring
alongside keyword intersection. Catches non-exact skill matches
where meaning overlaps but exact terms differ.

Example:
    User has "FastAPI" but JD says "Python web frameworks" →
    keyword match = 0%, semantic match = high similarity.

Uses multi-vector matching:
    - skills_embedding: user skills vs JD requirements
    - projects_embedding: project descriptions vs JD responsibilities
    - profile_embedding: full profile summary vs full JD

Combined score: (0.4 × keyword) + (0.6 × semantic)
"""

import os
import math
import logging
from typing import List, Optional, Dict

from app.schemas.user import FinalUserProfile

logger = logging.getLogger(__name__)

# Model configuration
EMBEDDING_MODEL = "text-embedding-004"


class EmbeddingService:
    """Semantic matching via Gemini Embedding API."""

    _client = None

    @classmethod
    def _get_client(cls):
        """Lazy-initialize the Gemini client."""
        if cls._client is None:
            try:
                from google import genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not set")
                cls._client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        return cls._client

    @classmethod
    async def embed_text(cls, text: str) -> List[float]:
        """
        Generate a 768-dimensional embedding for the given text
        using Gemini text-embedding-004.
        """
        if not text or len(text.strip()) < 5:
            return []

        try:
            client = cls._get_client()
            # Truncate to Gemini's input limit
            truncated = text[:8000]

            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=truncated,
            )

            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return []

    @classmethod
    def cosine_similarity(cls, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    @classmethod
    async def semantic_match(
        cls,
        user_profile: FinalUserProfile,
        jd_text: str,
    ) -> Dict:
        """
        Multi-vector semantic match scoring.

        Computes three separate similarity dimensions:
            1. Skills similarity: user skills text vs JD requirements text
            2. Projects similarity: project descriptions vs JD responsibilities
            3. Profile similarity: full profile summary vs full JD

        Returns:
            {
                "semantic_score": 78.5,  # 0–100 scale
                "skills_similarity": 0.82,
                "projects_similarity": 0.71,
                "profile_similarity": 0.76,
                "top_aligned_dimensions": ["Strong backend skills alignment", ...]
            }
        """
        try:
            # 1. Skills embedding
            user_skills_text = cls._build_skills_text(user_profile)
            jd_requirements_text = cls._extract_requirements_text(jd_text)

            skills_emb = await cls.embed_text(user_skills_text)
            jd_req_emb = await cls.embed_text(jd_requirements_text)
            skills_sim = cls.cosine_similarity(skills_emb, jd_req_emb) if skills_emb and jd_req_emb else 0.0

            # 2. Projects embedding
            user_projects_text = cls._build_projects_text(user_profile)
            projects_emb = await cls.embed_text(user_projects_text)
            jd_full_emb = await cls.embed_text(jd_text[:5000])
            projects_sim = cls.cosine_similarity(projects_emb, jd_full_emb) if projects_emb and jd_full_emb else 0.0

            # 3. Full profile embedding
            profile_text = cls._build_profile_text(user_profile)
            profile_emb = await cls.embed_text(profile_text)
            profile_sim = cls.cosine_similarity(profile_emb, jd_full_emb) if profile_emb and jd_full_emb else 0.0

            # Weighted combination (skills most important)
            semantic_score = (
                0.45 * skills_sim +
                0.30 * projects_sim +
                0.25 * profile_sim
            ) * 100  # Convert to 0–100

            # Identify aligned dimensions
            aligned = []
            if skills_sim > 0.75:
                aligned.append("Strong technical skills alignment with role requirements")
            elif skills_sim > 0.5:
                aligned.append("Moderate skills overlap — adjacent expertise detected")

            if projects_sim > 0.7:
                aligned.append("Project experience closely matches role responsibilities")
            elif projects_sim > 0.5:
                aligned.append("Projects demonstrate relevant domain experience")

            if profile_sim > 0.7:
                aligned.append("Overall profile strongly matches the role profile")

            return {
                "semantic_score": round(semantic_score, 1),
                "skills_similarity": round(skills_sim, 3),
                "projects_similarity": round(projects_sim, 3),
                "profile_similarity": round(profile_sim, 3),
                "top_aligned_dimensions": aligned,
            }

        except Exception as e:
            logger.error(f"Semantic matching failed: {e}")
            return {
                "semantic_score": None,
                "skills_similarity": None,
                "projects_similarity": None,
                "profile_similarity": None,
                "top_aligned_dimensions": [],
                "error": str(e),
            }

    @classmethod
    def _build_skills_text(cls, profile: FinalUserProfile) -> str:
        """Build a natural language skills description for embedding."""
        parts = [f"Technical skills: {', '.join(profile.skills[:25])}"]
        if profile.soft_skills:
            parts.append(f"Professional skills: {', '.join(profile.soft_skills[:10])}")

        # Add tech stacks from experience
        for exp in profile.experience[:3]:
            if exp.tech_stack:
                parts.append(f"Used {', '.join(exp.tech_stack[:5])} at {exp.organization}")

        return ". ".join(parts)

    @classmethod
    def _build_projects_text(cls, profile: FinalUserProfile) -> str:
        """Build project descriptions text for embedding."""
        parts = []
        for proj in profile.projects[:5]:
            desc = proj.description[0][:200] if proj.description else "project work"
            tech = ", ".join(proj.tech_stack[:5]) if proj.tech_stack else ""
            parts.append(f"{proj.title}: {desc}. Technologies: {tech}")
        return ". ".join(parts) if parts else "No projects listed"

    @classmethod
    def _build_profile_text(cls, profile: FinalUserProfile) -> str:
        """Build a full profile summary for embedding."""
        parts = []
        if profile.summary:
            parts.append(profile.summary)
        parts.append(f"Skills: {', '.join(profile.skills[:15])}")

        for exp in profile.experience[:3]:
            parts.append(f"{exp.title} at {exp.organization} ({exp.duration})")

        for proj in profile.projects[:3]:
            desc = proj.description[0][:100] if proj.description else ""
            parts.append(f"Project: {proj.title} - {desc}")

        return ". ".join(parts)

    @classmethod
    def _extract_requirements_text(cls, jd_text: str) -> str:
        """
        Extract the requirements/skills section from JD text.
        Falls back to full JD if no section headers found.
        """
        text_lower = jd_text.lower()

        # Try to find requirements section
        markers = [
            "requirements", "qualifications", "what you'll need",
            "must have", "skills required", "required skills",
            "what we're looking for", "essential skills",
        ]

        best_start = -1
        for marker in markers:
            idx = text_lower.find(marker)
            if idx != -1 and (best_start == -1 or idx < best_start):
                best_start = idx

        if best_start != -1:
            return jd_text[best_start:best_start + 3000]

        # Fallback — use the full JD
        return jd_text[:3000]

    @classmethod
    def blend_scores(
        cls,
        keyword_score: float,
        semantic_score: Optional[float],
    ) -> float:
        """
        Blend keyword and semantic scores.
        Formula: (0.4 × keyword) + (0.6 × semantic)
        Falls back to keyword-only if semantic is unavailable.
        """
        if semantic_score is None:
            return keyword_score

        return round(0.4 * keyword_score + 0.6 * semantic_score, 1)
