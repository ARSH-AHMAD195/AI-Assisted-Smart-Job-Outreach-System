import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from app.schemas.email import EmailRequest, EmailResponse

# Load environment variables
load_dotenv()

import json

class EmailService:
    @staticmethod
    async def generate_email(request: EmailRequest) -> EmailResponse:
        """
        Generate multiple email variants based on different outreach strategies.
        """
        from app.utils.ai_handler import AIHandler
        
        # Strategies defined in the prompt
        strategies = {
            "project-focused": "Focus on specific projects the candidate has built that align with the company's needs.",
            "skill-focused": "Highlight deep expertise in the core technical stack required for the role.",
            "curiosity-driven": "Focus on the company's engineering blog, recent releases, or specific technical challenges they might face."
        }
        
        # Prepare context
        skills_matched = ", ".join(request.job_match.matched_skills)
        projects_str = "\n".join([f"- {p.title}: {' '.join(p.description[:1])}" for p in request.user_profile.projects])
        
        system_prompt = "Act as a Highly Proactive Job Hunter and Expert Technical Copywriter. Your goal is to write a high-conversion, humane outreach email. Avoid using em dashes (—) in your writing."
        
        prompt = f"""
        Write a very "humane" and personalized outreach email from ME to the company.
        
        TONE/STRATEGY: {strategies.get(request.tone.lower(), strategies['project-focused'])}
        My Tone should be: "I saw the job description but I couldn't wait as job sites take time/are crowded, so I thought I should reach out directly. I went through your company website and mission, and I think I am a seamless fit."
        
        MY NAME: {request.user_profile.name}
        MATCHED SKILLS: {skills_matched}
        MY KEY PROJECTS:
        {projects_str}
        
        TARGET COMPANY: {request.recipient_name}
        JOB DESCRIPTION (Truncated): {request.jd_text[:2000]}
        
        COMPANY INTELLIGENCE (VERY IMPORTANT):
        {json.dumps(request.company_intel.dict()) if request.company_intel else "No specific intel gathered yet."}
        
        REQUIREMENTS:
        - Written from MY perspective (The Candidate).
        - Human-sounding, warm, and confident (not desperate).
        - Under 130 words.
        - Mention a specific detail from the COMPANY INTELLIGENCE to show I've done my homework.
        - Clear CTA (Ask for a brief 10-min chat).
        
        OUTPUT FORMAT (JSON ONLY):
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
                provider="auto"
            )
            
            # Extract JSON from text
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            return EmailResponse(
                subject_lines=[data.get("subject", "Following up on my application")],
                body=data.get("body", ""),
                personalization_points=data.get("personalization_points", []),
                generated_at=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Email generation error: {e}")
            return EmailResponse(
                subject_lines=["Technical Interest in Role"],
                body="I'm reaching out directly as I'm very interested in the role at your company. My skills align perfectly with your requirements.",
                personalization_points=[],
                generated_at=datetime.now().isoformat()
            )
