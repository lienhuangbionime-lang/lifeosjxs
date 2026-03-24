import os
from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

class ThinkingResult(BaseModel):
    insight: str = Field(..., description="A deep, reflective insight based on the user's input.")
    actionable_step: str = Field(..., description="One concrete, actionable next step.")
    philosophical_question: str = Field(..., description="A question to provoke deeper thought.")

class ThinkerAgent:
    def __init__(self):
        from app.core.gemini import get_gemini_client
        self.client = get_gemini_client()

    async def process(self, user_input: str) -> ThinkingResult:
        # Load System Prompt from external file
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "system_cortex.md")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except Exception:
            system_prompt = "You are Cortex. Help the user think deeper."

        from app.core.gemini import safe_generate_content, get_model
        model_info = get_model("smart")
        
        final_prompt = f"""
        {system_prompt}
        
        User Input: "{user_input}"
        """
        
        from app.core.gemini import safe_generate_content
        response = await safe_generate_content(
            client=self.client,
            prefer_mode="fast",
            contents=final_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ThinkingResult,
            },
        )
        
        return response.parsed
