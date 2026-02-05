# app/core/gemini.py
from typing import Literal, Dict
import os
import logging

# genai is the google-genai wrapper used in the project; defensive import
try:
    import genai
except Exception:
    genai = None

logger = logging.getLogger("app.core.gemini")

# read defaults from env (these are model ids)
DEFAULT_FAST = os.getenv("GEMINI_FAST_MODEL", "gemini-2.5-flash")
DEFAULT_SMART = os.getenv("GEMINI_SMART_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# perform genai.configure if possible
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("genai configured.")
    except Exception as e:
        logger.exception("Failed to configure genai: %s", e)
else:
    if not genai:
        logger.warning("genai library not available; gemini client factory will be limited.")
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set; genai won't be configured (offline/degraded mode).")


def get_model(mode: Literal["fast", "smart"] = "fast") -> Dict[str, str]:
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

        return {"model": model, "configured": bool(GEMINI_API_KEY)}
    except Exception as e:
        logger.exception("Error in get_model: %s", e)
        return {"model": DEFAULT_FAST, "configured": False}