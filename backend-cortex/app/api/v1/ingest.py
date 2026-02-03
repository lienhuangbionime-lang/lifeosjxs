# 檔案位置: backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
import json
import logging
from datetime import datetime

# 引入核心設定與資料庫
from app.core.config import settings
from app.core.database import supabase
from app.models.gemini import LogAnalysisResult 

router = APIRouter()
logger = logging.getLogger("uvicorn")

# 定義前端傳來的請求格式
class LogRequest(BaseModel):
    text: str
    date: str

@router.post("/ingest", response_model=LogAnalysisResult)
async def ingest_log(request: LogRequest):
    """
    接收前端日誌 -> 透過 Gemini 進行思考 -> 存入 Supabase 海馬迴 -> 回傳結果
    """
    try:
        logger.info(f"📥 Cortex received log for {request.date}")
        
        # 1. 檢查並啟動 Gemini
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="Missing GEMINI_API_KEY")
            
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.MODEL_SMART)
        
        prompt = f"Analyze this log for {request.date}: {request.text}"
        
        # 2. 執行思考 (Thinking)
        response = model.generate_content(
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": LogAnalysisResult.model_json_schema(),
            },
        )
        
        # 3. 解析結果 (Parsing)
        raw_json = response.text
        structured_data = json.loads(raw_json)
        logger.info("✅ Gemini analysis complete.")

        # 4. 寫入海馬迴 (Memory Consolidation)
        # 準備要寫入 Supabase 的 payload
        db_payload = {
            "date": request.date,
            "content": structured_data["markdown_body"],
            "mood": structured_data["meta"]["metrics"]["mood"],
            "focus": structured_data["meta"]["metrics"]["focus"],
            "energy": structured_data["meta"]["metrics"]["energy"],
            "structured_data": structured_data, # 存入完整的 JSON 分析結果
            "created_at": datetime.now().isoformat()
        }

        # 執行 Upsert (有則更新，無則新增)
        data, count = supabase.table("logs").upsert(db_payload).execute()
        logger.info(f"💾 Memory stored in Hippocampus.")

        # 5. 回傳給前端 (Feedback)
        return structured_data

    except Exception as e:
        logger.error(f"🔥 Cortex Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
