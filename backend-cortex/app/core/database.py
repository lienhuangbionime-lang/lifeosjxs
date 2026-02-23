# app/core/database.py
from typing import Optional
import os
import logging

try:
    from supabase import create_client, Client
except Exception:  # defensive: package might not be installed in some envs
    create_client = None
    Client = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.core.database")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Optional["Client"] = None

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.warning(
        "SUPABASE_URL or SUPABASE_KEY not provided. Running in offline/degraded mode (supabase=None). "
        "Set SUPABASE_URL and SUPABASE_KEY for database access."
    )
else:
    if create_client is None:
        logger.error(
            "supabase-py not available (create_client import failed). supabase client cannot be created."
        )
    else:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Simple connectivity check: try a lightweight request
            try:
                res = supabase.rpc("pg_sleep", {"seconds": 0}).execute()  # harmless call if pg extension exists; may fail silently
                logger.info("Supabase client created. Connectivity test executed.")
            except Exception:
                # fallback: attempt a generic select with no assumptions
                try:
                    _ = supabase.table("memories").select("id").limit(1).execute()
                    logger.info("Supabase client created and basic query executed.")
                except Exception:
                    # Not fatal: leave client available, just warn
                    logger.warning("Supabase client created but connectivity check failed. It may still work at runtime.")
        except Exception as e:
            logger.exception("Failed to create supabase client: %s", e)
            supabase = None

def get_supabase_client() -> Client:
    # Explicit check if we want to enforce it, or just return Optional
    if supabase is None:
        # In production this might be fatal, or we can handle it at call site
        raise Exception("Supabase client is not initialized. Check SUPABASE_URL and SUPABASE_KEY.")
    return supabase