from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.agents.sorter import SorterAgent

router = APIRouter()
agent = SorterAgent()

class IngestRequest(BaseModel):
    content: str
    source: str = "web"

@router.post("/ingest")
async def ingest_log(request: IngestRequest):
    try:
        # 1. AI 思考與結構化
        structured_log = agent.process(request.content)
        
        # 2. (TODO) 這裡未來會呼叫 Supabase 寫入 DB
        # database.save(structured_log)
        
        return {
            "status": "success", 
            "data": structured_log.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
