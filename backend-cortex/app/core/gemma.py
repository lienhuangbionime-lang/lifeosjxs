# app/core/gemma.py
from typing import Literal, Dict, Any
import os
import logging
import asyncio

try:
    from fastapi import Request
except ImportError:
    Request = None  # type: ignore

from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger("app.core.gemma")

# [v5.4] No hardcoded model defaults — all model IDs come from the dynamic registry.
# Run: python tools/quota_probe.py  to refresh the registry with live quota data.
GEMMA_API_KEY = os.getenv("GEMINI_API_KEY")

# Discovery Service (v3.9) - Lazy import to avoid circular dependencies
def get_discovery_service():
    from app.services.model_discovery import model_discovery
    return model_discovery

# Global primitive for key; client is managed via factory to ensure loop safety
GEMMA_API_KEY = os.getenv("GEMMA_API_KEY")

_client_registry = {}

def get_gemma_client():
    """
    Returns a Gemma client bound to the current event loop.
    Prevents 'attached to a different loop' errors in async environments.
    """
    if not GEMMA_API_KEY or not genai:
        return None
        
    loop = asyncio.get_event_loop()
    loop_id = id(loop)
    
    if loop_id not in _client_registry:
        try:
            _client_registry[loop_id] = genai.Client(api_key=GEMMA_API_KEY)
            logger.info(f"Gemma client initialized for loop {loop_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemma client for loop {loop_id}: {e}")
            return None
            
    return _client_registry[loop_id]

# Legacy compatibility for modules importing the global directly
gemma_client = get_gemma_client() if genai and GEMMA_API_KEY else None



import json

# Registry Resolution (v5.6)
# Standardized to look for sync_brain at the project root (lifeosjxs/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "sync_brain" / "model_registry.json"

def sanitize_model_name(name: str) -> str:
    """Ensures model names follow the exact identifiers required by the SDK."""
    if not name: return name
    s = name.strip().lower()
    if s.startswith("models/"):
        s = s.replace("models/", "", 1)
    return f"models/{s}"

def get_model(mode: Literal["fast", "smart"] = "fast") -> Dict[str, Any]:
    """[v5.5 Dynamic] Returns the best available model from the verified registry."""
    try:
        # 1. ENV override
        env_model = os.getenv("GEMMA_FAST_MODEL" if mode == "fast" else "GEMMA_SMART_MODEL")
        if env_model:
            return {"model": sanitize_model_name(env_model), "configured": bool(GEMMA_API_KEY)}

        # 2. Dynamic registry (populated by test.py probe)
        if REGISTRY_PATH.exists():
            try:
                import json
                reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
                # Note: test.py saves 'verified_models' as a flat list
                candidates = reg.get("verified_models", [])
                
                # Filter by tier-relevant substrings if needed, or just take first
                if candidates:
                    # Logic: 3.1 or 2.0-flash-lite for 'fast', pro for 'smart'
                    if mode == "fast":
                        # Prefer 1.5-flash or 2.0-flash over 'lite' variants if present
                        fast_tier = [c for c in candidates if "flash" in c and "lite" not in c] or \
                                    [c for c in candidates if "flash" in c] or candidates
                        return {"model": sanitize_model_name(fast_tier[0]), "configured": bool(GEMMA_API_KEY)}
                    else:
                        smart_tier = [c for c in candidates if "pro" in c] or \
                                     [c for c in candidates if "2.0-flash" in c] or candidates
                        return {"model": sanitize_model_name(smart_tier[0]), "configured": bool(GEMMA_API_KEY)}
            except Exception as e:
                logger.error(f"Failed to parse registry: {e}")

        # 3. Last Resort fallback (Hardcoded to known active ID)
        return {"model": "models/gemma-flash-lite-latest", "configured": bool(GEMMA_API_KEY)}
        
    except Exception as e:
        logger.exception("Error in get_model: %s", e)
        return {"model": "models/gemma-flash-lite-latest", "configured": False}

async def get_embeddings(text: str) -> list[float]:
    """
    Generate vector embeddings for given text using Gemma.
    Dimension: 3072 (Full Precision Protocol)
    [v4.1] Added retry logic for 429 errors.
    """
    if not gemma_client:
        return []
    
    # Embedding models to try in order (Verified 2026-03-24: gemma-embedding-2-preview is active)
    embedding_models = [
        "models/gemini-embedding-2-preview", 
        "models/gemini-embedding-001"
    ]
    
    for model_id in embedding_models:
        try:
            # Flexible configuration per model capability
            config_args = {
                "task_type": "RETRIEVAL_DOCUMENT",
                "title": "Cortex Memory"
            }
            # Only apply 3072 if using the standard text-embedding-004 (Full Precision Protocol)
            if "004" in model_id:
                config_args["output_dimensionality"] = 3072

            result = await gemma_client.aio.models.embed_content(
                model=model_id,
                contents=text,
                config=types.EmbedContentConfig(**config_args)
            )
            if result.embeddings and len(result.embeddings) > 0:
                return result.embeddings[0].values
            return []
        except Exception as e:
            error_msg = str(e)
            if any(err in error_msg for err in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                logger.warning(f"Embedding model {model_id} throttled or unavailable ({error_msg}). Retrying next model...")
            else:
                logger.error(f"Failed to generate embeddings with {model_id}: {e}")
            continue # Try the next model in the chain
    return []


def get_request_gemma_client(request: "Request"):
    """
    FastAPI dependency: returns a per-request Gemma client.
    If the caller provides X-Gemma-Key header, a dedicated client is created.
    Falls back to the global gemma_client from env.
    """
    req_key = request.headers.get("X-Gemma-Key")
    if req_key and genai:
        try:
            return genai.Client(api_key=req_key)
        except Exception as e:
            logger.warning(f"[WARN] Could not create per-request Gemma client: {e}")
    return get_gemma_client()  # fallback to global with loop safety
    
async def safe_generate_content(
    client: Any, 
    prefer_mode: Literal["fast", "smart"],
    contents: Any,
    config: Any = None,
    system_instruction: Any = None
) -> Any:
    """
    [v4.2 Advanced Quota Defense]
    Executes a content generation with automatic failover AND exponential backoff.
    Attempts to cycle through all available tiers if quota is exhausted.
    """
    import random
    
    # 1. Determine Tier Chain
    modes_to_try = [prefer_mode]
    if prefer_mode == "smart":
        modes_to_try.append("fast")
    else:
        modes_to_try.append("smart")
    
    # 2. Emergency model list — dynamically sourced from registry, not hardcoded.
    # Includes both available and quota-exhausted as a last resort.
    try:
        discovery = get_discovery_service()
        emergency_models = (
            discovery.verified_models.get("fast", []) +
            discovery.verified_models.get("smart", []) +
            discovery.pending_models.get("fast", []) +
            discovery.pending_models.get("smart", [])
        )
        # Also add quota-exhausted models as absolute last resort (they may recover)
        _reg = getattr(discovery, "_raw_registry", {})
        if hasattr(discovery, "quota_exhausted"):
            emergency_models += discovery.quota_exhausted.get("fast", [])
            emergency_models += discovery.quota_exhausted.get("smart", [])
    except Exception:
        emergency_models = []  # will raise from tier chain if this fails too
    
    last_error = None
    actual_config = None
    
    # --- Try Preferred & Alternative Tiers ---
    for mode in modes_to_try:
        model_info = get_model(mode)
        model_id = model_info["model"]
        
        # [v7.1 Turbo] Shallow Backoff for 503s to ensure fast failover to other tiers
        # Mobile users cannot wait 40 seconds.
        backoff_delays = [0, 1.0, 3.0]
        
        for delay in backoff_delays:
            if delay > 0:
                # Add a tiny jitter to avoid synchronized retries
                await asyncio.sleep(delay + random.uniform(0, 0.5))
                logger.info(f"Retrying tier {mode} ({model_id}) after {delay}s backoff...")
                
            try:
                actual_config = config or {}
                if system_instruction:
                    if isinstance(actual_config, dict):
                        actual_config["system_instruction"] = system_instruction
                    else:
                        actual_config.system_instruction = system_instruction
                
                response = await client.aio.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=actual_config
                )
                return response
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if any(err in error_msg for err in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                    logger.warning(f"Tier {mode} ({model_id}) temporarily unavailable ({error_msg}) at delay {delay}s.")
                    continue # Try next backoff delay
                else:
                    break # Critical non-429 error, don't retry this model
        
        # If we exhausted all backoffs for this tier, go to next tier in modes_to_try
        continue
                
    # 3. Final Emergency attempt (if everything in preferred chain failed with 429 or 503)
    is_exhausted = last_error and any(err in str(last_error) for err in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"])
    if is_exhausted:
        for em_model in emergency_models:
            try:
                logger.warning(f"Preferred chain exhausted. Using emergency: {em_model}")
                return await client.aio.models.generate_content(
                    model=em_model,
                    contents=contents,
                    config=actual_config or config
                )
            except Exception as ee:
                if "429" in str(ee) or "RESOURCE_EXHAUSTED" in str(ee):
                    continue
                logger.error(f"Emergency model {em_model} failed: {ee}")
            
    raise last_error or Exception("Failover chain exhausted")

async def multimodal_interpret(file_data: bytes, mime_type: str, prompt: str = "Describe this content in detail and extract all key information. If it's a document, provide a structured summary. Language: Traditional Chinese.") -> str:
    """
    [v4.1] Unified Multimodal Helper with Failover.
    """
    client = get_gemma_client()
    if not client:
        return "[Error: Gemma Multimodal not configured]"
        
    try:
        # Use safe_generate_content for multimodal too
        response = await safe_generate_content(
            client=client,
            prefer_mode="fast",
            contents=[
                prompt,
                types.Part.from_bytes(data=file_data, mime_type=mime_type)
            ]
        )
        return response.text
    except Exception as e:
        logger.error(f"Multimodal interpret failed: {e}")
        return f"[Error interpreting file: {str(e)}]"
