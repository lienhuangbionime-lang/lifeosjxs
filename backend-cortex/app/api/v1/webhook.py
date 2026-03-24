from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
import json
from datetime import datetime
from app.services.rag_service import rag_service
from app.core.database import get_request_client

router = APIRouter()
logger = logging.getLogger("cortex.webhook")

@router.post("/v1/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    [The Omni-Gateway]
    Receives signals from OpenClaw, WhatsApp, or other external perception layers.
    """
    try:
        payload = await request.json()
        logger.info(f"📥 [WEBHOOK] Received payload: {json.dumps(payload)[:200]}")
        
        # 1. Basic Validation (HMAC or Token)
        # TODO: Implement robust verification
        
        # 2. Extract Data
        source = payload.get("source", "unknown")
        content = payload.get("content", "")
        sender = payload.get("sender", "unknown")
        
        if not content:
            return {"status": "ignored", "reason": "empty content"}

        # 3. Queue Ingestion (Background Task to avoid timeout)
        background_tasks.add_task(process_webhook_payload, payload)
        
        return {"status": "accepted", "source": source}
        
    except Exception as e:
        logger.error(f"❌ [WEBHOOK ERROR] {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

async def process_webhook_payload(payload: Dict):
    """
    Process the payload: Archive to Memories and notify Cortex if urgent.
    """
    content = payload.get("content", "")
    source = payload.get("source", "webhook")
    
    # Ingest into 'memories' via RAG service
    try:
        await rag_service.ingest_text(
            text=content,
            meta={
                "source": source,
                "type": "webhook_signal",
                "sender": payload.get("sender"),
                "timestamp": datetime.utcnow().isoformat()
            },
            target="memories"
        )
        logger.info(f"✅ [WEBHOOK] Signal ingested into memories from {source}")
    except Exception as e:
        logger.error(f"❌ [WEBHOOK INGEST ERROR] {e}")
