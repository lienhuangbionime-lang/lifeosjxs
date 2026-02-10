from datetime import date
from app.core.database import supabase
import logging

logger = logging.getLogger("cortex.usage")

async def track_usage(tokens: int = 0):
    """Increment daily usage counter"""
    try:
        today = date.today().isoformat()
        
        # Upsert: request_count + 1, token_usage + tokens
        # Supabase doesn't support atomic increment easily via simple client without RPC
        # But we can try RPC if defined, or read-modify-write (race condition risk but acceptable for personal app)
        
        # Better: Use RPC if possible. If not, use on_conflict upsert
        
        # 1. Try to get current
        res = supabase.table("system_usage").select("*").eq("date", today).execute()
        
        if res.data:
            current = res.data[0]
            new_count = current["request_count"] + 1
            new_tokens = current["token_usage"] + tokens
            supabase.table("system_usage").update({
                "request_count": new_count,
                "token_usage": new_tokens
            }).eq("id", current["id"]).execute()
        else:
            supabase.table("system_usage").insert({
                "date": today,
                "request_count": 1,
                "token_usage": tokens
            }).execute()
            
    except Exception as e:
        logger.error(f"Failed to track usage: {e}")

async def get_daily_usage() -> dict:
    """Get usage for today"""
    try:
        today = date.today().isoformat()
        res = supabase.table("system_usage").select("*").eq("date", today).execute()
        if res.data:
            return res.data[0]
        return {"request_count": 0, "token_usage": 0}
    except Exception as e:
        logger.error(f"Failed to get usage: {e}")
        return {"request_count": 0, "token_usage": 0}
