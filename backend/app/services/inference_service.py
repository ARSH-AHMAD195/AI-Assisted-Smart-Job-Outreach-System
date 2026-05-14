import os
from groq import Groq
from app.schemas.user import FinalUserProfile
from typing import List, Dict
import json
from dotenv import load_dotenv

load_dotenv()

class InferenceService:
    @staticmethod
    async def infer_roles(profile: FinalUserProfile) -> List[Dict]:
        """
        Infer likely job roles based on skills, experience, and projects.
        Returns a list of roles with confidence scores.
        """
        from app.utils.ai_handler import AIHandler
        
        skills_str = ", ".join(profile.skills)
        experience_summary = "\n".join([f"- {exp.title} at {exp.organization}" for exp in profile.experience])
        projects_summary = "\n".join([f"- {proj.title}: {proj.description[0] if proj.description else ''}" for proj in profile.projects])
        
        system_prompt = "You are an AI Career Strategist. Analyze candidate profiles and infer target job roles."
        prompt = f"""
        Analyze the following candidate profile and infer the top 3-5 job roles they are best suited for.
        
        CANDIDATE PROFILE:
        - Skills: {skills_str}
        - Experience:
        {experience_summary}
        - Projects:
        {projects_summary}
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "roles": [
                {{"role": "Role Name", "confidence": 0.95, "reason": "Brief reason why"}},
                ...
            ]
        }}
        """
        
        try:
            result_text = await AIHandler.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                provider="auto"
            )
            
            # Extract JSON from text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            if isinstance(data, dict) and "roles" in data:
                return data["roles"]
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            print(f"Error parsing role inference: {e}")
            return []
