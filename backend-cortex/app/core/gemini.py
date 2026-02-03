# backend-cortex/app/core/gemini.py (Bypass Version)
import requests
import json
from app.core.config import get_settings

settings = get_settings()

class GeminiClient:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = model_name
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

    def generate_content(self, prompt: str):
        if not self.api_key:
            return MockResponse("⚠️ Error: GEMINI_API_KEY not found.")
            
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # 構建 Payload
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "response_mime_type": "application/json"
            }
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status() # 檢查 HTTP 錯誤
            data = response.json()
            
            # 解析回應文字
            text_content = data['candidates']['content']['parts']['text']
            return MockResponse(text_content)
            
        except Exception as e:
            print(f"❌ Gemini API Error: {str(e)}")
            # 回傳一個假的回應物件，避免 ingest.py 崩潰
            return MockResponse(json.dumps({
                "markdown_body": f"⚠️ 連線失敗: {str(e)}",
                "meta": {"metrics": {"mood": 5, "focus": 5, "energy": 5}},
                "tasks": []
            }))

# 模擬 SDK 的回應物件
class MockResponse:
    def __init__(self, text):
        self.text = text

# 工廠函數 (保持與原本介面一致)
def get_model(model_type: str = "fast"):
    model_name = settings.MODEL_FAST if model_type == "fast" else settings.MODEL_SMART
    return GeminiClient(model_name=model_name)