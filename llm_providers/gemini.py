import os
import google.generativeai as genai


class GeminiClient:
    def __init__(self, model: str = "gemini-1.5-flash-002", temperature: float = 0.3):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set — please export your Gemini API key first.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": temperature,
                "top_p": 0.9,
            },
        )

    def infer(self, system_prompt: str, jd: str, cv: str) -> str:
        """
        Compare Job Description and CV using Gemini.
        Returns raw JSON text.
        """
        prompt = f"""{system_prompt}

---
[JD]
{jd}

---
[CV]
{cv}

Return ONLY valid JSON as specified above.
"""
        response = self.model.generate_content(prompt)
        return response.text
