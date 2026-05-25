"""
Variant Generator Service — generates recipient-type-aware outreach email variants.

Each contact type (recruiter, engineering, founder, hr, careers) gets a
distinct email with tailored tone, style, and content focus. This prevents
repetitive outreach patterns and improves authenticity.

Leverages the existing AIHandler for dual-provider AI generation (Gemini/Groq).
"""

import json
import logging
from typing import Dict, Optional

from app.utils.ai_handler import AIHandler

logger = logging.getLogger(__name__)


# Strategy configurations per recipient type
VARIANT_STRATEGIES: Dict[str, Dict[str, str]] = {
    "recruiter": {
        "style": "concise_role_focused",
        "description": (
            "Concise & role-focused. Highlight matched skills and role fit. "
            "Keep it under 100 words. Get straight to the point — recruiters "
            "read hundreds of emails daily."
        ),
        "tone": "Professional, direct, respectful of recruiter's time",
        "focus": "Role alignment, key qualifications, availability",
    },
    "recruiting": {
        "style": "concise_role_focused",
        "description": (
            "Concise & role-focused for the recruiting team. Emphasize "
            "relevant experience and cultural fit. Under 100 words."
        ),
        "tone": "Professional, direct, team-aware",
        "focus": "Experience match, team fit, process awareness",
    },
    "engineering": {
        "style": "technical_project",
        "description": (
            "Technical & project-oriented. Reference specific projects, "
            "tech stack alignment, open-source contributions, and engineering "
            "culture. Show technical depth and genuine curiosity."
        ),
        "tone": "Peer-to-peer technical enthusiasm, collaborative",
        "focus": "Technical projects, stack overlap, engineering challenges",
    },
    "founder": {
        "style": "vision_oriented",
        "description": (
            "Product & vision-oriented. Connect personal mission to the "
            "company's vision. Show awareness of the company's journey, "
            "recent milestones, and growth stage."
        ),
        "tone": "Ambitious, mission-driven, collaborative, startup-aware",
        "focus": "Vision alignment, impact potential, growth mindset",
    },
    "hr": {
        "style": "structured_professional",
        "description": (
            "Clear and structured. Focus on qualifications, cultural fit, "
            "and availability. Be warm but process-aware."
        ),
        "tone": "Warm, professional, structured, process-aware",
        "focus": "Qualifications, cultural alignment, logistics",
    },
    "careers": {
        "style": "balanced_professional",
        "description": (
            "Balanced professional outreach. Combine skills with genuine "
            "company understanding. Show you've done your homework."
        ),
        "tone": "Enthusiastic but measured, well-researched",
        "focus": "Skills + company knowledge, genuine interest",
    },
    "general": {
        "style": "balanced_professional",
        "description": (
            "General professional outreach. Lead with strongest qualifications "
            "and show genuine interest in the company."
        ),
        "tone": "Professional, approachable, authentic",
        "focus": "Core strengths, company interest, availability",
    },
}


class VariantGeneratorService:
    """Generates outreach email variants tailored to recipient personas."""

    @classmethod
    async def generate_single_variant(
        cls,
        recipient_type: str,
        company_name: str,
        job_title: str,
        job_description: str,
        company_intel: Optional[Dict] = None,
        user_profile_summary: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_role: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate a single email variant for a specific recipient type.

        Args:
            recipient_type: Contact type (recruiter, engineering, founder, etc.)
            company_name: Target company name
            job_title: Job title being applied for
            job_description: Job description text
            company_intel: Optional company intelligence dict
            user_profile_summary: Optional user profile summary
            recipient_name: Optional name of the recipient (e.g. from HR contact list)
            recipient_role: Optional role/title of the recipient

        Returns:
            Dict with keys: subject, body, style
        """
        strategy = VARIANT_STRATEGIES.get(
            recipient_type.lower(),
            VARIANT_STRATEGIES["general"]
        )

        # Build company intelligence context
        intel_context = "No specific intelligence gathered yet."
        if company_intel:
            intel_parts = []
            if company_intel.get("vision"):
                intel_parts.append(f"Vision: {company_intel['vision']}")
            if company_intel.get("products"):
                intel_parts.append(f"Products: {', '.join(company_intel['products'][:5])}")
            if company_intel.get("tech_stack"):
                intel_parts.append(f"Tech Stack: {', '.join(company_intel['tech_stack'][:8])}")
            if company_intel.get("engineering_culture"):
                intel_parts.append(f"Culture: {company_intel['engineering_culture']}")
            if intel_parts:
                intel_context = "\n".join(intel_parts)

        system_prompt = (
            "Act as a Highly Proactive Job Hunter and Expert Technical Copywriter. "
            "Your goal is to write a high-conversion, humane outreach email. "
            "Avoid using em dashes in your writing. "
            "Each email must feel unique and personally crafted."
        )

        recipient_context = ""
        if recipient_name:
            recipient_context = f"\nRECIPIENT NAME: {recipient_name}"
            if recipient_role:
                recipient_context += f" ({recipient_role})"

        prompt = f"""
Write a personalized outreach email from ME (the candidate) to {company_name}.
{recipient_context}

OUTREACH STRATEGY: {strategy['style']}
STRATEGY DESCRIPTION: {strategy['description']}
DESIRED TONE: {strategy['tone']}
FOCUS AREAS: {strategy['focus']}

RECIPIENT TYPE: {recipient_type}
TARGET COMPANY: {company_name}
JOB TITLE: {job_title}
JOB DESCRIPTION (Truncated): {job_description[:2000]}

COMPANY INTELLIGENCE:
{intel_context}

{"MY PROFILE: " + user_profile_summary if user_profile_summary else ""}

REQUIREMENTS:
- Written from MY perspective (the candidate).
- Human-sounding, warm, and confident (not desperate).
- Under 130 words.
- Greet the recipient by name if a RECIPIENT NAME is provided above (e.g., "Hi Akanksha," or "Dear Akanksha,").
- If company intelligence is available, mention a specific detail to show research.
- Clear CTA: ask for a brief 10-min chat or express interest.
- Do NOT use generic phrases like "I'm excited to apply" or "I believe I'm a great fit".
- Make it conversational and genuine.
- The email MUST feel different from a mass template.

OUTPUT FORMAT (JSON ONLY, no markdown):
{{
    "subject": "...",
    "body": "...",
    "personalization_points": ["...", "..."]
}}
"""

        try:
            result_text = await AIHandler.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                provider="auto",
            )

            # Extract JSON from response
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            data = json.loads(result_text)

            return {
                "subject": data.get("subject", f"Interest in {job_title} at {company_name}"),
                "body": data.get("body", ""),
                "style": strategy["style"],
                "personalization_points": data.get("personalization_points", []),
            }

        except Exception as e:
            logger.error(f"Variant generation failed for {recipient_type}: {e}")
            # Fallback: generate a basic email
            return cls._fallback_variant(
                recipient_type, company_name, job_title, strategy
            )

    @classmethod
    def _fallback_variant(
        cls,
        recipient_type: str,
        company_name: str,
        job_title: str,
        strategy: Dict[str, str],
    ) -> Dict[str, str]:
        """Generate a minimal fallback email when AI generation fails."""
        fallback_bodies = {
            "recruiter": (
                f"Hi,\\n\\nI came across the {job_title} role at {company_name} and "
                f"wanted to reach out directly. My background aligns well with the "
                f"requirements, and I'd love a quick 10-minute chat to discuss how "
                f"I could contribute to your team.\\n\\nBest regards"
            ),
            "engineering": (
                f"Hi,\\n\\nI noticed the {job_title} opening at {company_name} and "
                f"was drawn to the technical challenges involved. I've been working "
                f"on similar problems and would love to discuss potential synergies. "
                f"Would you have 10 minutes for a quick call?\\n\\nCheers"
            ),
            "founder": (
                f"Hi,\\n\\nI've been following {company_name}'s journey and the "
                f"{job_title} role caught my eye. Your vision resonates with my "
                f"professional goals, and I'd love to explore how I could contribute "
                f"to what you're building.\\n\\nBest"
            ),
        }

        body = fallback_bodies.get(
            recipient_type,
            fallback_bodies["recruiter"].replace("recruiter", recipient_type)
        )

        return {
            "subject": f"Interest in {job_title} at {company_name}",
            "body": body,
            "style": strategy["style"],
            "personalization_points": [],
        }
