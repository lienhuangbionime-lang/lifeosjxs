# app/core/gemini.py
from typing import Literal, Dict, Any
import os
import logging

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore

# genai is the modern google.genai wrapper used in the project; defensive import
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger("app.core.gemini")

# read defaults from env (these are model ids)
DEFAULT_FAST = os.getenv("GEMINI_FAST_MODEL", "gemini-flash-lite-latest")
DEFAULT_SMART = os.getenv("GEMINI_SMART_MODEL", "gemini-pro-latest")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = None

# instantiate genai Client if possible
if genai and GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("gemini_client configured.")
    except Exception as e:
        logger.exception("Failed to configure genai: %s", e)
else:
    if not genai:
        logger.warning("google.genai library not available; gemini client factory will be limited.")
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; genai won't be configured (offline/degraded mode).")



def sanitize_model_name(name: str) -> str:
    """
    Ensures model names follow the exact identifiers required by the SDK.
    Prevents common mismatches and ensures IDs are in 'models/...' format.
    """
    if not name:
        return name
        
    s = name.strip().lower()
    
    # Remove prefix if exists for easier matching
    if s.startswith("models/"):
        s = s.replace("models/", "", 1)
    
    # Strict mapping dictionary (Aligned with LifeOSvs-main quality proven models)
    # Strict mapping dictionary for SDK v1 available models
    mapping = {
        "gemini-3.1": "gemini-3.1-pro-preview",
        "gemini-3.0": "gemini-3-pro-preview",
        "gemini-33": "gemini-3-pro-preview", 
        "gemini-3": "gemini-3-pro-preview",
        "gemini-2.5": "gemini-2.5-flash",
        "gemini-1.5-pro": "gemini-pro-latest",         # 1.5 not available, mapped to pro-latest
        "gemini-1.5-flash-latest": "gemini-flash-latest", # mapped to flash-latest
        "gemini-1.5-flash": "gemini-flash-latest",
        "gemini-flash-lite-latest": "gemini-flash-lite-latest", 
        "gemini-flash-lite": "gemini-flash-lite-latest",
        "gemini-lite": "gemini-flash-lite-latest",
        "gemini-pro-latest": "gemini-pro-latest",
        "gemini-pro": "gemini-pro-latest", 
    }
    
    # Check if the name starts with any of our known prefixes (sorted by length descending to match 3.1 before 3)
    sorted_prefixes = sorted(mapping.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if s.startswith(prefix):
            return f"models/{mapping[prefix]}"
            
    # Default: Ensure models/ prefix
    return f"models/{s}"

def get_model(mode: Literal["fast", "smart"] = "fast") -> Dict[str, Any]:
    """
    Client factory that returns model configuration for the requested mode.
    Returns a simple dict with model id and an info string.
    This function intentionally avoids importing other app.core modules to prevent circular imports.
    """
    try:
        if mode == "fast":
            model = os.getenv("GEMINI_FAST_MODEL", DEFAULT_FAST)
        elif mode == "smart":
            model = os.getenv("GEMINI_SMART_MODEL", DEFAULT_SMART)
        else:
            logger.warning("Unknown mode '%s' requested, defaulting to fast", mode)
            model = DEFAULT_FAST

        from app.core.gemini import sanitize_model_name
        return {"model": sanitize_model_name(model), "configured": bool(GEMINI_API_KEY)}
    except Exception as e:
        logger.exception("Error in get_model: %s", e)
        return {"model": DEFAULT_FAST, "configured": False}

async def get_embeddings(text: str) -> list[float]:
    """
    Generate vector embeddings for given text using Gemini.
    Dimension: 3072 (Full Precision Protocol)
    """
    if not gemini_client:
        return []
        
    try:
        result = await gemini_client.aio.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                title="Cortex Memory",
                output_dimensionality=3072
            )
        )
        if result.embeddings and len(result.embeddings) > 0:
            return result.embeddings[0].values
        return []
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return []


def get_request_gemini_client(request: "Request"):
    """
    FastAPI dependency: returns a per-request Gemini client.
    If the caller provides X-Gemini-Key header, a dedicated client is created.
    Falls back to the global gemini_client from env.
    """
    req_key = request.headers.get("X-Gemini-Key")
    if req_key and genai:
        try:
            return genai.Client(api_key=req_key)
        except Exception as e:
            logger.warning(f"[WARN] Could not create per-request Gemini client: {e}")
    return gemini_client  # fallback to global
