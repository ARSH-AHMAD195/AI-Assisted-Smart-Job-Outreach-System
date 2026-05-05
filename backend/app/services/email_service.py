import os
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
from app.schemas.email import EmailRequest, EmailResponse

# Load environment variables
load_dotenv()

# Configure Groq (fast + free tier is generous)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class EmailService:
    @staticmethod
    def generate_email(request: EmailRequest) -> EmailResponse:
        # Prepare context for the prompt
        skills_matched = ", ".join(request.job_match.matched_skills)
        skills_missing = ", ".join(request.job_match.missing_skills)
        projects = []
        for p in request.user_profile.projects:
            projects.append(f"- {p.title}: {' '.join(p.description[:2])}")
        projects_str = "\n".join(projects)
        
        prompt = f"""
        Act as a Senior Career Coach and Expert Technical Copywriter.
        Your task is to write a highly personalized, high-conversion outreach email for a candidate.

        CANDIDATE PROFILE:
        - Name: {request.user_profile.name}
        - Key Skills: {', '.join(request.user_profile.skills)}
        - Relevant Projects:
        {projects_str}

        JOB DESCRIPTION CONTEXT:
        - JD Content: {request.jd_text[:1500]}
        - Match Analysis: {request.job_match.analysis}
        - Matched Skills: {skills_matched}
        - Missing Skills: {skills_missing}

        REQUIREMENTS:
        1. Tone: {request.tone}
        2. Recipient: {request.recipient_name}
        3. Logic:
           - Start with a strong hook related to the company/JD.
           - Mention specific projects that prove fit for the "Matched Skills".
           - Briefly and confidently address any major "Missing Skills" by highlighting adaptability or related experience.
           - Include a clear Call to Action (CTA).
        
        OUTPUT FORMAT (follow this EXACTLY):
        SUBJECTS: subject line 1 | subject line 2 | subject line 3
        BODY: the full email body text here
        POINTS: point 1 | point 2 | point 3
        """

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        text = response.choices[0].message.content

        # Parse the structured output
        try:
            subjects_start = text.find("SUBJECTS:") + 9
            subjects_end = text.find("BODY:")
            subjects_raw = text[subjects_start:subjects_end].strip()
            subjects = [s.strip().strip('"\'') for s in subjects_raw.split("|")]

            body_start = text.find("BODY:") + 5
            body_end = text.find("POINTS:")
            body = text[body_start:body_end].strip()

            points_start = text.find("POINTS:") + 7
            points_raw = text[points_start:].strip()
            points = [p.strip().strip('"\'- ') for p in points_raw.split("|") if p.strip()]
        except:
            subjects = ["Application for Open Role", "Exploring Opportunities", "Technical Fit Discussion"]
            body = text
            points = ["Personalized based on profile"]

        return EmailResponse(
            subject_lines=subjects[:3],
            body=body,
            personalization_points=points[:4],
            generated_at=datetime.now().isoformat()
        )
