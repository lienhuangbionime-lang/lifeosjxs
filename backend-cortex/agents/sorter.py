import os
from google import genai
from dotenv import load_dotenv
from app.models.gemini import LogEntry

load_dotenv()

class SorterAgent:
    def __init__(self):
        # 使用 Flash 模型進行快速分類
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_name = "gemini-2.0-flash" 

    def process(self, user_input: str) -> LogEntry:
        prompt = f"""
        你是一個極速分類器 (The Sorter)。
        請分析以下使用者輸入，並將其結構化。
        
        使用者輸入: {user_input}
        """
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": LogEntry, # 關鍵：強制結構化輸出
            },
        )
        
        # 自動轉為 Pydantic Object，無需再做 JSON.parse
        return response.parsed
