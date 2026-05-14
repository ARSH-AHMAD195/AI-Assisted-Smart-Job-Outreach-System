import os
import logging
from typing import Optional, Dict, Any
from google import genai
from groq import Groq

logger = logging.getLogger(__name__)

class AIHandler:
    _groq_client = None
    _gemini_client = None

    @classmethod
    def _get_groq_client(cls):
        if not cls._groq_client:
            cls._groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        return cls._groq_client

    @classmethod
    def _get_gemini_client(cls):
        if not cls._gemini_client:
            # Initializes using the GEMINI_API_KEY environment variable automatically
            cls._gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return cls._gemini_client

    @classmethod
    async def generate_content(cls, prompt: str, system_prompt: str = "", provider: str = "auto") -> str:
        """
        Generates content using either Groq or Gemini.
        If 'auto', it picks Gemini for long prompts/complex tasks.
        """
        # Determine provider
        if provider == "auto":
            # Heuristic: If prompt is very long, use Gemini
            provider = "gemini" if len(prompt) > 4000 else "groq"

        if provider == "gemini":
            try:
                client = cls._get_gemini_client()
                full_prompt = f"{system_prompt}\n\nUser Input:\n{prompt}"
                # Reverting to 1.5-flash which often has separate quota/better availability
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=full_prompt
                )
                return response.text
            except Exception as e:
                logger.error(f"Gemini failed: {e}. Falling back to Groq.")
                provider = "groq"

        if provider == "groq":
            try:
                client = cls._get_groq_client()
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                # Updated to a supported, active model
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.error(f"Groq failed: {e}")
                return "Error: AI generation failed."

        return "Error: Unsupported provider."
