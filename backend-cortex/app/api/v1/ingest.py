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
from app.models.schemas import LogEntrySchema # 確保您有定義這個

router = APIRouter()
logger = logging.getLogger("cortex.ingest")

# 定義請求格式 (對應前端 fetch body)
class IngestRequest(BaseModel):
    text: str
    date: str  # YYYY-MM-DD

@router.post("/")
async def ingest_log(request: IngestRequest):
    logger.info(f"🧠 Cortex receiving input for {request.date}...")
    
    try:
        # 1. 呼叫 Gemini (The Architect)
        model = get_model("smart") # 使用 Pro 模型進行深度分析
        
        # System Prompt (精簡版)
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
        
        # 產生內容
        response = model.generate_content(f"{system_prompt}\n\n{user_content}")
        
        # 2. 解析 JSON (防禦性解析)
        try:
            cleaned_text = response.text.strip()
            # 移除可能的 markdown code block 標記
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            ai_data = json.loads(cleaned_text)
        except Exception as e:
            logger.error(f"JSON Parse Error: {e}")
            # 降級處理：回傳原始文字
            ai_data = {
                "markdown_body": request.text, 
                "meta": {"metrics": {}}, 
                "tasks": []
            }

        # 3. 寫入海馬迴 (Supabase)
        # [Fix] 這裡強制使用小寫 'logentry'，解決 Table Not Found 問題
        db_payload = {
            "date": request.date,
            "note": ai_data.get("markdown_body", request.text), # 注意：Supabase 欄位名需對應 (可能是 content 或 note)
            "mood": ai_data.get("meta", {}).get("metrics", {}).get("mood", 5),
            "is_ai": True,
            "created_at": datetime.datetime.now().isoformat()
        }

        if supabase:
            try:
                # 嘗試寫入 (使用 logentry 小寫)
                data, count = supabase.table("logentry").insert(db_payload).execute()
                logger.info("✅ Memory stored in Hippocampus.")
            except Exception as db_e:
                logger.error(f"❌ Database Write Failed: {db_e}")
                # 注意：這裡不拋出錯誤，讓前端仍能收到 AI 分析結果，只是沒存檔
        
        # 4. 回傳給前端 (Body)
        return {
            "success": True,
            "model": "gemini-2.0-flash", # 或動態讀取
            "data": ai_data
        }

    except Exception as e:
        logger.error(f"🔥 Ingest Critical Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))