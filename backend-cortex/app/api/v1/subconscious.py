from fastapi import APIRouter, HTTPException
import logging
from app.services.subconscious import run_autonomous_reflection

router = APIRouter()
logger = logging.getLogger("cortex.api.subconscious")

@router.post("/reflect")
async def manual_reflection():
    """
    Manually triggers the Subconscious Reflection process.
    """
    try:
        logger.info("🧠 [API] Manual Subconscious Reflection triggered by user.")
        result = await run_autonomous_reflection(hours_lookback=48)
        
        if result:
            return {"success": True, "data": result, "message": "Reflection completed and stored."}
        else:
            return {"success": False, "message": "Not enough data or AI failed to reflect."}
            
    except Exception as e:
        logger.error(f"Manual reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
