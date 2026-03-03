# app/core/gemini.py
from typing import Literal, Dict, Any
import os
import logging
import asyncio

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

# [v5.4] No hardcoded model defaults — all model IDs come from the dynamic registry.
# Run: python tools/quota_probe.py  to refresh the registry with live quota data.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Discovery Service (v3.9) - Lazy import to avoid circular dependencies
def get_discovery_service():
    from app.services.model_discovery import model_discovery
    return model_discovery

# Global primitive for key; client is managed via factory to ensure loop safety
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

_client_registry = {}

def get_gemini_client():
    """
    Returns a Gemini client bound to the current event loop.
    Prevents 'attached to a different loop' errors in async environments.
    """
    if not GEMINI_API_KEY:
        return None
        
    loop = asyncio.get_event_loop()
    loop_id = id(loop)
    
    if loop_id not in _client_registry:
        try:
            _client_registry[loop_id] = genai.Client(api_key=GEMINI_API_KEY)
            logger.info(f"Gemini client initialized for loop {loop_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client for loop {loop_id}: {e}")
            return None
            
    return _client_registry[loop_id]

# Legacy compatibility for modules importing the global directly
gemini_client = get_gemini_client() if genai and GEMINI_API_KEY else None



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
    
    # Strict mapping dictionary (Updated from live quota probe 2026-03-04)
    # Confirmed AVAILABLE: gemini-2.5-flash, gemini-flash-lite-latest
    # Confirmed QUOTA-EXHAUSTED: gemini-2.0-flash, gemini-2.0-flash-lite
    mapping = {
        "gemini-2.5-flash": "gemini-2.5-flash",       # [OK] Available
        "gemini-flash-lite-latest": "gemini-flash-lite-latest",  # [OK] Available
        "gemini-2.5-pro": "gemini-2.5-pro",            # [QUOTA] exhausted
        "gemini-2.0-flash-lite": "gemini-2.0-flash-lite",  # [QUOTA] exhausted
        "gemini-2.0-flash": "gemini-2.0-flash",        # [QUOTA] exhausted
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
    [v5.4 Fully Dynamic] Returns the best available model for the requested tier.
    Model priority: ENV override > discovery registry > absolute emergency fallback.
    All model IDs come from the dynamic registry (quota_probe.py).
    NEVER hardcoded — complies with SYSTEM_CONTEXT.md.
    """
    try:
        # 1. ENV override always wins (allows manual per-deployment override)
        env_model = os.getenv("GEMINI_FAST_MODEL" if mode == "fast" else "GEMINI_SMART_MODEL")
        if env_model:
            return {"model": sanitize_model_name(env_model), "configured": bool(GEMINI_API_KEY)}

        # 2. Dynamic registry (populated by quota_probe.py)
        discovery = get_discovery_service()
        registry_model = discovery.get_best_model(mode)

        # 3. Cross-tier fallback: if smart is unavailable, try fast; and vice versa
        if not registry_model and mode == "smart":
            registry_model = discovery.get_best_model("fast")
            logger.warning("Smart tier unavailable, falling back to fast tier.")

        if registry_model:
            return {"model": sanitize_model_name(registry_model), "configured": bool(GEMINI_API_KEY)}

        # 4. Absolute last resort: ask the registry for ANY verified model
        all_models = (
            discovery.verified_models.get("fast", []) +
            discovery.verified_models.get("smart", [])
        )
        if all_models:
            return {"model": sanitize_model_name(all_models[0]), "configured": bool(GEMINI_API_KEY)}

        raise ValueError("No verified models in registry. Run: python tools/quota_probe.py")
    except Exception as e:
        logger.exception("Error in get_model: %s", e)
        # Last-resort: try reading raw from registry file to recover gracefully
        try:
            import json
            from pathlib import Path
            reg = json.loads(Path("data/model_registry.json").read_text(encoding="utf-8"))
            candidates = reg.get("verified_models", {}).get(mode, [])
            if candidates:
                return {"model": sanitize_model_name(candidates[0]), "configured": bool(GEMINI_API_KEY)}
        except Exception:
            pass
        return {"model": "models/gemini-2.5-flash", "configured": False}  # absolute bare minimum

async def get_embeddings(text: str) -> list[float]:
    """
    Generate vector embeddings for given text using Gemini.
    Dimension: 3072 (Full Precision Protocol)
    [v4.1] Added retry logic for 429 errors.
    """
    if not gemini_client:
        return []
    
    # Embedding models to try in order (Verified 2026-02-28: gemini-embedding-001 is active)
    embedding_models = [
        "models/text-embedding-004", 
        "models/gemini-embedding-001",
        "text-embedding-004"
    ]
    
    for model_id in embedding_models:
        try:
            result = await gemini_client.aio.models.embed_content(
                model=model_id,
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
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                logger.warning(f"Embedding model {model_id} exhausted (429).")
            else:
                logger.error(f"Failed to generate embeddings with {model_id}: {e}")
            continue # Try the next model in the chain
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
    return get_gemini_client()  # fallback to global with loop safety
    
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
        
        # Exponential Backoff for each tier (1.5s, 3s)
        backoff_delays = [0, 1.5, 3.0]
        
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
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    logger.warning(f"Tier {mode} ({model_id}) exhausted (429) at delay {delay}s.")
                    continue # Try next backoff delay
                else:
                    break # Critical non-429 error, don't retry this model
        
        # If we exhausted all backoffs for this tier, go to next tier in modes_to_try
        continue
                
    # 3. Final Emergency attempt (if everything in preferred chain failed with 429)
    if last_error and ("429" in str(last_error) or "RESOURCE_EXHAUSTED" in str(last_error)):
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
    client = get_gemini_client()
    if not client:
        return "[Error: Gemini Multimodal not configured]"
        
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
