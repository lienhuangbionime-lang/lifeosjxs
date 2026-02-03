# 檔案: backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
import json
import logging
import os

# 引入核心設定與模型
from app.core.config import settings
from app.models.gemini import LogAnalysisResult # 確保這個檔案存在並與之前定義的一致

router = APIRouter()
# 設定 Logger 以便除錯
logger = logging.getLogger("uvicorn")

# 定義前端傳來的請求格式
class LogRequest(BaseModel):
    text: str
    date: str

@router.post("/ingest", response_model=LogAnalysisResult)
async def ingest_log(request: LogRequest):
    """
    接收前端日誌 -> 透過 Gemini 進行結構化分析 (Structure) -> 回傳 Pydantic 物件
    """
    try:
        logger.info(f"📥 Cortex received: {request.text[:50]}...")

        # 1. 設定 Gemini (確保 API Key 已載入)
        if not settings.GEMINI_API_KEY:
             raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in env")
             
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.MODEL_SMART)

        # 2. 準備 Prompt
        prompt = f"""
        Analyze the following user log for date: {request.date}.
        Convert it into the structured format defined by the JSON schema.
        
        USER INPUT:
        {request.text}
        """

        # 3. 呼叫 AI (啟用結構化輸出)
        # [CTO Note] 這邊使用 response_json_schema 強制輸出的格式
        response = model.generate_content(
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": LogAnalysisResult.model_json_schema(),
            },
        )

        # 4. [關鍵修復] 安全地解析回應
        # 不去手動存取 candidates['content'] (這會導致 list indices error)
        # 直接使用 SDK 提供的 .text 屬性，它會自動提取生成的文字
        raw_json = response.text 
        
        # 確保 AI 回傳的是有效 JSON
        try:
            parsed_data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.error(f"❌ JSON Decode Error. Raw: {raw_json}")
            raise HTTPException(status_code=500, detail="AI response was not valid JSON.")

        logger.info("✅ Gemini analysis complete.")
        
        # 5. 回傳字典 (FastAPI 會自動將其驗證為 LogAnalysisResult)
        return parsed_data

    except Exception as e:
        logger.error(f"🔥 Cortex Error: {str(e)}")
        # 回傳包含錯誤訊息的 JSON，而不是讓伺服器崩潰
        # 注意：這裡我們拋出 HTTPException，前端會捕捉到並顯示 Alert
        raise HTTPException(status_code=500, detail=f"Cortex Error: {str(e)}")