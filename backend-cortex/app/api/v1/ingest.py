# backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.gemini import get_model
import json
import datetime

router = APIRouter()

class LogRequest(BaseModel):
    text: str
    date: str

# 定義我們希望 AI 回傳的嚴格結構 (Prompt Engineering)
SYSTEM_PROMPT = """
你是 LifeOS v3.1 的核心整理者 (The Sorter)。
請分析使用者的輸入，並輸出符合以下 JSON 結構的回應：
{
  "markdown_body": "整理後的 Markdown 筆記，包含標題、重點摘要",
  "meta": {
    "metrics": {
      "mood": 1-10 (整數),
      "focus": 1-10 (整數),
      "energy": 1-10 (整數)
    },
    "tags": ["tag1", "tag2"],
    "date": "YYYY-MM-DD"
  },
  "tasks": [
    {"title": "任務名稱", "status": "PENDING"}
  ]
}
"""

@router.post("/ingest")
async def ingest_log(request: LogRequest):
    try:
        # 1. 取得快速模型 (Flash Layer)
        model = get_model(model_type="fast")
        
        # 2. 準備提示詞
        user_prompt = f"Date: {request.date}\nContent: {request.text}"
        
        # 3. 發送給 Gemini
        print(f"🤖 Calling Gemini for: {request.text[:20]}...")
        response = model.generate_content(f"{SYSTEM_PROMPT}\n\n{user_prompt}")
        
        # 4. 解析結果
        result_json = json.loads(response.text)
        
        return {
            "success": True,
            "model": model.model_name,
            "data": result_json
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # 即使失敗，也要回傳結構化的錯誤，不要讓前端崩潰 (防禦性編程)
        return {
            "success": False,
            "error": str(e),
            "data": {
                "markdown_body": f"⚠️ AI 處理失敗，原始內容已保存：\n\n{request.text}",
                "meta": {"metrics": {"mood": 5, "focus": 5, "energy": 5}},
                "tasks": []
            }
        }