# app/api/v1/memories.py
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
import asyncio
import os
import sys

from app.models.schemas import LogEntrySchema
from app.core.database import supabase
from app.core.vector import vector_engine

router = APIRouter()
logger = logging.getLogger("app.api.v1.memories")


# --- Internal Helpers ---
async def create_memory_entry(content: str, source: str = "system", tags: List[str] = [], date: Optional[str] = None):
    """
    Internal helper to create a memory entry.
    Used by: tasks.py (completion logs), ingest.py (daily logs), etc.
    """
    if not date:
        from app.core.time_utils import get_today_str_taipei
        date = get_today_str_taipei()
        
    entry = {
        "date": date,
        "content": content,
        "category": source, # Use 'source' as category
        "is_ai": True if source == "system" else False,
        "tags": tags
    }
    
    try:
        res = supabase.table("memories").insert(entry).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise e

# --- Endpoints ---

@router.post("/", response_model=dict)
async def add_memory(entry: LogEntrySchema):
    """
    Manual memory insertion endpoint.
    """
    data = await create_memory_entry(
        content=entry.content,
        date=entry.date,
        tags=entry.tags or [],
        source="manual_api"
    )
    return {"success": True, "data": data}

@router.get("/", response_model=List[LogEntrySchema])
async def get_recent_memories(
    limit: int = 20,
    q: Optional[str] = Query(None, description="Search query (semantic or keyword)")
):
    """
    Retrieve memories.
    - If `q` is provided: Performs Semantic Search (Vector).
    - If `q` is None: Returns recent memories (Chronological).
    """
    if supabase is None:
        logger.warning("Supabase client unavailable; cannot fetch memories.")
        raise HTTPException(status_code=503, detail="Database unavailable (supabase not configured).")

    try:
        # Case 1: Semantic Search
        if q and len(q.strip()) > 0:
            # Run vector search in thread pool
            def vector_search():
                results = vector_engine.search_memories(supabase, q, limit=limit)
                
                # [Schema Alignment]
                # RPC returns {id, content, metadata(json), similarity}
                # Pydantic expects flat {id, content, date, tags, mood...}
                mapped_results = []
                for row in results:
                    meta = row.get("metadata", {}) or {}
                    mapped_results.append({
                        "id": row.get("id"),
                        "content": row.get("content"),
                        "date": meta.get("date") or row.get("date"),
                        "tags": meta.get("tags", []) or row.get("tags", []),
                        "category": meta.get("category") or row.get("category"),
                        "mood": meta.get("mood", 5),
                        "focus": meta.get("focus", 5),
                        "energy": meta.get("energy", 5),
                        "is_ai": False, # Default for search results if not in metadata
                        "ai_model": None
                    })
                return mapped_results
            
            loop = asyncio.get_running_loop()
            data = await loop.run_in_executor(None, vector_search)
            return data

        # Case 2: Recent Memories (Chronological)
        # supabase client is sync; run in thread to avoid blocking event loop
        def query():
            try:
                result = supabase.table("memories").select("*").order("date", desc=True).limit(limit).execute()
                return result
            except Exception as e:
                # bubble up
                raise

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, query)

        # supabase-py returns a dict-like object or APIResponse object
        if hasattr(result, "data"):
            data = result.data
        elif isinstance(result, dict):
            data = result.get("data")
        else:
            data = None

        error = None
        if hasattr(result, "error"):
            error = result.error
        elif isinstance(result, dict):
            error = result.get("error")

        if error:
            logger.error("Supabase error while fetching memories: %s", error)
            raise HTTPException(status_code=500, detail="Database query error")

        return data or []

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error fetching memories: %s", e)
        raise HTTPException(status_code=500, detail="Unexpected error fetching memories")


# --- Monthly Review Endpoints ---

@router.get("/review/{year}/{month}")
async def get_monthly_review(year: int, month: int):
    """
    Get the monthly review for a specific month.
    """
    if not supabase:
        raise HTTPException(status_code=503, detail="Database unavailable")
    
    try:
        # Table name is "MonthlyReview"
        res = supabase.table("MonthlyReview").select("*").eq("year", year).eq("month", month).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching monthly review: {e}")
        return None 

@router.post("/review/{year}/{month}/generate")
async def trigger_monthly_review(year: int, month: int):
    """
    Trigger background generation of monthly review.
    """
    try:
        import subprocess
        
        # Run the script as a subprocess
        # Using sys.executable ensures we use the same python environment
        # The unified equipment is housed in the root /tools directory now
        script_path = os.path.join("..", "tools", "generate_monthly_review.py")
        
        # Use Popen to run in background
        process = subprocess.Popen(
            [sys.executable, script_path, str(year), str(month)],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            cwd=os.getcwd() # Run from project root
        )
        
        return {"status": "started", "pid": process.pid, "message": "Generation started in background"}
    except Exception as e:
        logger.error(f"Failed to trigger review generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))