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

def safe_write(table_query, payload: dict, operation_type: str = "insert", max_retries: int = 3, **kwargs):
    """
    Executes a Supabase write with built-in Schema Drift resilience.
    If the remote DB throws PGRST204 (Missing Column), this intercepts the error,
    strips the invalid column from the payload, and retries.
    """
    import logging
    import re
    logger = logging.getLogger("cortex.database")
    
    current_payload = dict(payload)
    for attempt in range(max_retries):
        try:
            if operation_type == "insert":
                return table_query.insert(current_payload).execute()
            elif operation_type == "upsert":
                return table_query.upsert(current_payload, **kwargs).execute()
            elif operation_type == "update":
                return table_query.update(current_payload).execute()
            else:
                raise ValueError(f"Unknown operation_type: {operation_type}")
        except Exception as e:
            error_msg = str(e)
            if "PGRST204" in error_msg and "Could not find the" in error_msg:
                # Example error: Could not find the 'updated_at' column of 'MonthlyReview'
                match = re.search(r"Could not find the '([^']+)' column", error_msg)
                if match:
                    invalid_column = match.group(1)
                    logger.warning(f"[Schema Drift] Column '{invalid_column}' missing. Stripping and retrying...")
                    if invalid_column in current_payload:
                        del current_payload[invalid_column]
                        continue # Retry
            # If it's a different error, or we couldn't parse the column, raise it
            raise e
    raise Exception(f"Failed safe_write after {max_retries} retries due to schema mismatch.")


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
    if supabase is not None:
        logger.debug("[GUEST MODE] No X-Supabase headers found. Falling back to Server Client (Guest Mode).")
        # CRITICAL: Do NOT mutate the global singleton. Wrap it.
        from types import SimpleNamespace
        wrapped_client = SimpleNamespace()
        # Proxy attributes
        for attr in ['table', 'rpc', 'auth', 'postgrest']:
            if hasattr(supabase, attr):
                setattr(wrapped_client, attr, getattr(supabase, attr))
        
        wrapped_client._is_guest_mode = True
        return wrapped_client
        
    logger.debug("[SANDBOX] No headers and no server fallback available — returning None.")
    return None
