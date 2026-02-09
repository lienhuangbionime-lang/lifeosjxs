from fastapi import APIRouter
from pydantic import BaseModel
import logging
import datetime
from app.core.gemini import get_model, genai

router = APIRouter()
logger = logging.getLogger("cortex.analyze")

class AnalyzeRequest(BaseModel):
    month: str

@router.post("/monthly")
async def analyze_monthly(request: AnalyzeRequest):
    # 1. 初始化模型
    model_config = get_model("smart")
    model_name = model_config.get("model", "gemini-3.0-pro-preview")
    model = genai.GenerativeModel(model_name)

    # 2. 模擬或是從 Supabase 讀取資料 (這裡先簡化，直接生成策略)
    # TODO: 讀取 Supabase 的 LogEntry
    
    prompt = f"""
    You are a strategic life coach (CCA). Analyze the month: {request.month}.
    Provide a strategy in valid JSON format:
    {{
        "success": true,
        "data": {{
            "strategy": {{
                "focus_project": "Project Name",
                "new_habits": ["Habit 1", "Habit 2"]
            }},
            "content": "Detailed markdown analysis..."
        }}
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        # 簡單解析 (建議之後改為更嚴謹的 JSON Parser)
        import json
        text = response.text.strip()
        text = response.text.strip()
        # Robust JSON extraction
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)
        return json.loads(text)
    except Exception as e:
        logger.error(f"Analyze failed: {e}")
        return {
            "success": False, 
            "error": str(e)
        }
