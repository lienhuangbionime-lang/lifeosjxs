# 檔案位置: backend-cortex/app/api/v1/ingest.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import json
import datetime

# 引入核心模組
from app.core.gemini import get_model
from app.core.database import supabase
from app.models.schemas import LogEntrySchema 

router = APIRouter()
logger = logging.getLogger("cortex.ingest")

# 定義請求格式
class IngestRequest(BaseModel):
    text: str
    date: str  # YYYY-MM-DD

# [CRITICAL FIX] 修正路由路徑
# 配合 main.py 的 prefix="/api/v1"，組合後路徑為 /api/v1/ingest
@router.post("/ingest") 
async def ingest_log(request: IngestRequest):
    logger.info(f"🧠 Cortex receiving input for {request.date}...")
    
    try:
        # 1. 呼叫 Gemini (The Architect)
        # 確保您的 get_model 支援 "smart" 參數，或改為 "gemini-2.0-flash"
        model = get_model("smart") 
        
        system_prompt = """
        You are the LifeOS Cortex. Analyze the user's daily log.
        Output MUST be valid JSON with this structure:
        {
            "markdown_body": "Cleaned log content with markdown formatting",
            "meta": {
                "date": "YYYY-MM-DD",
                "metrics": { "mood": 5, "focus": 5, "energy": 5 }
            },
            "tasks": [ {"title": "Task name", "status": "PENDING"} ],
            "tags": ["tag1", "tag2"]
        }
        """
        
        user_content = f"Date: {request.date}\nLog: {request.text}"
        
        response = model.generate_content(f"{system_prompt}\n\n{user_content}")
        
        # 2. 解析 JSON
        try:
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            ai_data = json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            ai_data = {
                "markdown_body": request.text, 
                "meta": {"metrics": {}}, 
                "tasks": []
            }

        # 3. 寫入海馬迴 (Supabase)
        # [Check] 確認使用了小寫 "logentry"
        db_payload = {
            "date": request.date,
            "note": ai_data.get("markdown_body", request.text),
            "mood": ai_data.get("meta", {}).get("metrics", {}).get("mood", 5),
            "is_ai": True,
            "created_at": datetime.datetime.now().isoformat()
        }

        if supabase:
            try:
                # 再次確認 Table Name 為小寫
                data, count = supabase.table("logentry").insert(db_payload).execute()
                logger.info("✅ Memory stored in Hippocampus.")
            except Exception as db_e:
                logger.error(f"❌ Database Write Failed: {db_e}")
                # 不拋出錯誤，讓前端仍能顯示分析結果
        
        # 4. 回傳給前端
        return {
            "success": True,
            "model": "gemini-2.0-flash", # 更新顯示的模型名稱
            "data": ai_data
        }

    except Exception as e:
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))