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
        # 使用 Flash 模型，但 Prompt 設定為思考者
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash" 

    def process(self, user_input: str) -> ThinkingResult:
        prompt = f"""
        You are Cortex, a highly advanced AI "Second Brain" designed to help the user think deeper, not just organize data.
        Your goal is to be a reflective mirror, a philosopher, and a strategic coach.
        
        Analyze the user's input below. Do NOT just summarize it.
        Instead:
        1. Identify the underlying emotion or core challenge.
        2. Offer a reframing or a philosophical perspective.
        3. Suggest a tiny, immediate next step.
        4. Ask a question that cuts to the heart of the matter.

        User Input: "{user_input}"

        Output must be in Traditional Chinese (繁體中文), but keep the tone sophisticated and warm.
        """
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ThinkingResult,
            },
        )
        
        return response.parsed
