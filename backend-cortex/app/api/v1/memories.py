# app/api/v1/memories.py
from fastapi import APIRouter, HTTPException
from typing import List
import logging
import asyncio

from app.models.schemas import LogEntrySchema
from app.core.database import supabase

router = APIRouter()
logger = logging.getLogger("app.api.v1.memories")


@router.get("/", response_model=List[LogEntrySchema])
async def get_recent_memories(limit: int = 20):
    """
    Retrieve recent LogEntry rows from supabase 'LogEntry' table, ordered by date desc.
    If supabase client is not configured, returns HTTP 503.
    """
    if supabase is None:
        logger.warning("Supabase client unavailable; cannot fetch memories.")
        raise HTTPException(status_code=503, detail="Database unavailable (supabase not configured).")

    try:
        # supabase client is sync; run in thread to avoid blocking event loop
        def query():
            try:
                result = supabase.table("LogEntry").select("*").order("date", desc=True).limit(limit).execute()
                return result
            except Exception as e:
                # bubble up
                raise

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, query)

        # supabase-py returns a dict-like object with 'data' and 'error'
        data = getattr(result, "data", None) or result.get("data") if isinstance(result, dict) else None
        error = getattr(result, "error", None) or result.get("error") if isinstance(result, dict) else None

        if error:
            logger.error("Supabase error while fetching memories: %s", error)
            raise HTTPException(status_code=500, detail="Database query error")

        # map list of dicts to pydantic models will be handled by FastAPI response model
        return data or []
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching memories: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error fetching memories")