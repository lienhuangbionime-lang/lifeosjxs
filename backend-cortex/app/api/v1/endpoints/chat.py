# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.rag_service import rag_service
import logging

router = APIRouter()
logger = logging.getLogger("cortex.chat")

class ChatMessage(BaseModel):
    message: str

@router.post("/ingest")
async def ingest_content(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        count = 0
        if file:
            # Track usage
            from app.core.usage import track_usage
            await track_usage(1)
            count += await rag_service.ingest_file(file)
        if text:
            from app.core.usage import track_usage
            await track_usage(1)
            count += await rag_service.ingest_text(text, {"source": "manual_entry"})
            
        return {"success": True, "chunks_added": count}
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def chat_message(body: ChatMessage):
    try:
        # Return Streaming Response
        return StreamingResponse(
            rag_service.query(body.message), 
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
