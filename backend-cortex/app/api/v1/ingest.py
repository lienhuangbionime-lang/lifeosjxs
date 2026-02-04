# 檔案: backend-cortex/app/api/v1/ingest.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
# 注意：這裡假設您已經有 get_model 實作，若無請暫時用 mock
try:
    from app.core.gemini import get_model
except ImportError:
    # Fallback for dev without Gemini setup
    def get_model(mode): return None

router = APIRouter()

# 定義資料模型
class LogRequest(BaseModel):
    text: str
    date: str

class IngestResponse(BaseModel):
    success: bool
    model: str
    data: dict
    error: str | None = None

@router.post("/ingest", response_model=IngestResponse)
async def ingest_log(request: LogRequest):
    """
    接收前端日誌 -> Sorter Agent (Flash Model) -> 結構化輸出
    """
    print(f"📥 Cortex received ingest: {request.text[:30]}...")
    
    try:
        # 1. 嘗試獲取 AI 模型 (Flash Layer)
        client = get_model("fast") 
        
        response_text = ""
        model_name = settings.MODEL_SMART if hasattr(settings, 'MODEL_SMART') else "gemini-2.0-flash"

        if client:
            # 這裡未來要接上 Sorter Agent 的邏輯
            # 目前先做簡單的回應測試連線
            try:
                ai_resp = client.generate_content(f"請將此日誌轉換為 Markdown 格式並簡短摘要: {request.text}")
                response_text = ai_resp.text
            except Exception as e:
                print(f"⚠️ AI Generation failed: {e}")
                response_text = f"AI Processing Error, saved raw: {request.text}"
        else:
            response_text = f"AI Offline (Mock Mode): {request.text}"

        # 2. 建構符合前端 CaptureView 預期的回應
        return {
            "success": True,
            "model": model_name,
            "data": {
                "markdown_body": response_text,
                "meta": {
                    "metrics": {"mood": 5, "focus": 5, "energy": 5},
                    "date": request.date
                },
                "tasks": [] # 未來由 Agent 提取
            }
        }

    except Exception as e:
        print(f"🔥 Ingest Error: {str(e)}")
        return {
            "success": False,
            "model": "error",
            "data": {},
            "error": str(e)
        }