from fastapi import APIRouter, HTTPException
import logging
from app.services.subconscious import run_autonomous_reflection
from app.core.database import supabase

router = APIRouter()
logger = logging.getLogger("cortex.api.subconscious")

@router.post("/reflect")
async def manual_reflection():
    """
    Manually triggers the Subconscious Reflection process.
    """
    try:
        logger.info("🧠 [API] Manual Subconscious Reflection triggered by user.")
        result = await run_autonomous_reflection(hours_lookback=168)
        
        if result:
            return {"success": True, "data": result, "message": "Reflection completed and stored."}
        else:
            # Check if there are ANY memories in the database to give a better hint
            check = supabase.table("memories").select("id").limit(1).execute()
            hint = " (Note: No memories found in your database. Write a diary entry first!)" if not check.data else ""
            return {"success": False, "message": f"Not enough data in lookback window or AI failed to reflect.{hint}"}
            
    except Exception as e:
        logger.error(f"Manual reflection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
