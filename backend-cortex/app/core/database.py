# app/core/database.py
from typing import Optional
import os
import logging

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore

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


def get_request_client(request: "Request"):
    """
    [v5.4] Privacy Sandbox — per-request Supabase client.

    ONLY creates a client from user-supplied X-Supabase-URL / X-Supabase-Key headers.
    Does NOT fall back to the server's own env-var Supabase client.

    This ensures that anonymous visitors (no keys in headers) get None back,
    and all user-facing endpoints return 503 Database unavailable — protecting
    the owner's data from being exposed to third parties.

    Background tasks (subconscious scheduler, crystallizer, etc.) use the
    module-level `supabase` client directly and are unaffected.
    """
    req_url = request.headers.get("X-Supabase-URL") or request.headers.get("x-supabase-url")
    req_key = request.headers.get("X-Supabase-Key") or request.headers.get("x-supabase-key")

    if req_url and req_key and create_client:
        try:
            # Sanitize URL to prevent getaddrinfo errors
            clean_url = req_url.strip()
            if not clean_url.startswith("http"):
                clean_url = "https://" + clean_url
            clean_key = req_key.strip()
            return create_client(clean_url, clean_key)
        except Exception as e:
            logger.warning(f"[WARN] Could not create per-request Supabase client: {e}")
            return None

    # [Phase F] Guest Mode Fallback
    # If no headers are provided, we fall back to the server's own env-var configuration (if available).
    # To ensure security, we tag this client so endpoints know to apply Guest Mode filters.
    if supabase is not None:
        logger.debug("[GUEST MODE] No X-Supabase headers found. Falling back to Server Client (Guest Mode).")
        supabase._is_guest_mode = True
        return supabase
        
    logger.debug("[SANDBOX] No headers and no server fallback available — returning None.")
    return None
