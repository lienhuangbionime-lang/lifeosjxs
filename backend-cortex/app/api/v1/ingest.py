# 檔案位置: backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import json
import logging
import uuid  # [New] 用來生成身分證
import google.generativeai as genai
from datetime import datetime
from app.core.database import supabase
from dotenv import load_dotenv

# 1. 初始化環境
load_dotenv()
router = APIRouter()
logger = logging.getLogger("uvicorn")

# 設定 Google Gemini
GENAI_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_KEY:
    logger.warning("⚠️ GEMINI_API_KEY not found in .env")
else:
    genai.configure(api_key=GENAI_KEY)

# 2. 定義資料結構 (Schema)
class IngestRequest(BaseModel):
    text: str
    date: str

class Metrics(BaseModel):
    mood: int = Field(description="Mood score 1-10")
    focus: int = Field(description="Focus score 1-10")
    energy: int = Field(description="Energy score 1-10")

class MetaData(BaseModel):
    date: str
    metrics: Metrics

class TaskItem(BaseModel):
    title: str = Field(description="The content of the task")
    status: str = Field(description="Status: pending or done")

class LogEntrySchema(BaseModel):
    markdown_body: str = Field(description="Refined markdown content with headers")
    meta: MetaData
    tasks: list[TaskItem] = Field(description="Extracted tasks list")

# 3. 主要 API 端點
@router.post("/ingest")
async def ingest_log(request: IngestRequest):
    logger.info(f"📥 Cortex received log for {request.date}")

    try:
        # A. 準備模型
        model_name = os.getenv("MODEL_SMART", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        
        system_prompt = """
        You are the 'Sorter Agent' of LifeOS v3.1.
        Analyze the raw input log. 
        1. Convert it into clean Markdown.
        2. Extract metrics (mood, focus, energy) based on sentiment.
        3. Extract any tasks mentioned.
        Output MUST be strict JSON matching the schema.
        """
        
        full_prompt = f"{system_prompt}\n\nUser Input ({request.date}):\n{request.text}"

        # B. 呼叫 Gemini
        response = model.generate_content(
            contents=full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json",
                response_schema=LogEntrySchema
            )
        )
        
        # C. 解析回應
        parsed_data = json.loads(response.text)
        metrics = parsed_data['meta']['metrics']
        
        # D. 寫入 Supabase (海馬迴)
        if supabase:
            # 準備 ISO 時間格式
            iso_date = f"{request.date}T00:00:00.000Z"
            
            # [Fix] 生成唯一 ID
            # 如果是 Upsert (更新)，Supabase 會根據 on_conflict 忽視這個 ID (如果該日期已存在)
            # 如果是 Insert (新增)，這個 ID 就會被當作主鍵
            row_id = str(uuid.uuid4())

            log_data = {
                "id": row_id, # ✅ 這裡補上了缺失的身分證
                "date": iso_date,
                "content": parsed_data['markdown_body'],
                "mood": metrics['mood'],
                "focus": metrics['focus'],
                "energy": metrics['energy'],
                "isAi": True,
                "aiModel": model_name,
                "updatedAt": datetime.now().isoformat()
            }
            
            # 2. 寫入主表
            data, count = supabase.table("LogEntry").upsert(log_data, on_conflict="date").execute()
            
            logger.info(f"✅ Log saved to Supabase (LogEntry): {request.date}")
        else:
            logger.warning("⚠️ Database disconnected: Skipping save.")

        return {
            "success": True,
            "data": parsed_data,
            "model": model_name
        }

    except Exception as e:
        logger.error(f"🔥 Cortex Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
