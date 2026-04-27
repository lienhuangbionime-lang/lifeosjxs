from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Any, Optional, Dict
from skills.e_nav.schema import NomadEntity, MenuItem, NomadMenu
from skills.e_nav.vision_engine import digitize_menu_with_gemma_3
from skills.e_nav.perception import ingest_nomads_task
from skills.e_nav.executor import compare_logistics_prices
from app.core.database import get_request_client
import logging
import base64

router = APIRouter()
logger = logging.getLogger("cortex.enav")

@router.get("/nomads", response_model=List[NomadEntity])
async def get_nomads(db: Any = Depends(get_request_client)):
    """?ûÂÇ≥Â∏∂Ê?Ë∑ùÈõ¢?ÅAI Ë©ïÂ??Å‰?Ê∫êÊ?Á±§Á? List??""
    try:
        if db:
            result = db.table("nomad_entities").select("*").order("trust_score", desc=True).execute()
            if result.data:
                return [NomadEntity.model_validate(row) for row in result.data]
        
        # Fallback to local sample if DB is empty or unavailable
        return [
            NomadEntity(
                name="ÈºéÊ≥∞Ë±?,
                cuisine="?∞Â??ôÁ?",
                trust_score=96,
                distance_text="350m",
                image_url="https://images.unsplash.com/photo-1555126634-323283e090fa?w=800&q=80",
                has_soul_bond=True,
                is_synced=True,
                menu_data=[{"name": "Â∞èÁ???, "price": 220, "is_soul_food": True}]
            )
        ]
    except Exception as e:
        logger.error(f"Failed to fetch nomads: {e}")
        return []

@router.post("/digitize", response_model=NomadMenu)
async def digitize_menu(payload: dict):
    """?•Êî∂ Base64 ?ñÁ?ÔºåÂ??≥Á?ÊßãÂ??ÑË???JSON??""
    image_base64 = payload.get("image")
    if not image_base64:
        raise HTTPException(status_code=400, detail="Missing 'image' in payload")
    
    try:
        # Decode base64
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        image_bytes = base64.b64decode(image_base64)
        
        return await digitize_menu_with_gemma_3(image_bytes)
    except Exception as e:
        logger.error(f"Digitization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logistics")
async def get_logistics(place_id: str):
    """?πÊ? place_id ?ûÂÇ≥?ÑÂπ≥?∞Á??ãË≤ª??ETA??""
    return compare_logistics_prices(place_id)

@router.post("/ingest")
async def trigger_ingestion():
    """?ãÂ?Ëß∏ÁôºÂ§ñÈÉ®Ë≥áÊ??ìÂ? (‰æãÂ?ÔºöÈ??öÂè∞????""
    try:
        nomads = await ingest_nomads_task()
        return {"status": "success", "count": len(nomads)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
