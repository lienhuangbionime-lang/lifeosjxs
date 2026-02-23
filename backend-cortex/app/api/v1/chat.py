
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import json
import asyncio
from pathlib import Path
from app.core.gemini import get_model, gemini_client
from google import genai

router = APIRouter()
logger = logging.getLogger("cortex.chat")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    model: Optional[str] = None
    url_context: Optional[Dict] = None  # {url, type, title, content} from url_fetch

# ---------------------------------------------------------------------------
# [Phase C] Short-Term Memory: inject last 5 evolution_log entries
# ---------------------------------------------------------------------------
_BASE_SYSTEM_PROMPT = """
[SYSTEM PROTOCOL: CodeSpeak Paradigm Active]
You are Cortex, the digital extension of the user's mind (LifeOS).
Your goal is to help the user manage their projects, clarify their thoughts, and retrieve memories with zero boilerplate.

- OUTPUT: High-signal, intentional, and concise. No conversational filler.
- FORMAT: Use structured Markdown.
- MEMORY ACCESS: You have access to the user's Memory Bank via the "## Relevant Context" section below.
- HALLUCINATION CONTROL: If the context is empty or says "NO MEMORIES FOUND", state exactly: "No relevant records found. Ask to create one."
- GLASS BOX: Expose your reasoning layer implicitly in your output structure.
"""

def build_system_prompt() -> str:
    """Builds the system prompt with recent evolution_log entries injected as short-term memory."""
    recent_events = ""
    try:
        # Try both relative path and absolute fallback
        for evo_path in [
            Path("sync_brain/evolution_log.json"),
            Path(r"c:\Users\lien.huang\AppData\lifeosjxs\sync_brain\evolution_log.json")
        ]:
            if evo_path.exists():
                with open(evo_path, encoding="utf-8") as f:
                    logs = json.load(f)
                last5 = logs[-5:]
                recent_events = "\n".join(
                    f"- [{e.get('timestamp', '')[:10]}] [{e.get('type', '')}] {e.get('event', '')}: {e.get('description', '')[:120]}"
                    for e in last5
                )
                break
    except Exception as e:
        logger.warning(f"[WARN] Could not load evolution_log: {e}")

    if recent_events:
        return f"""{_BASE_SYSTEM_PROMPT}
---
## System Short-Term Memory (Last 5 Events)
{recent_events}
---
"""
    return _BASE_SYSTEM_PROMPT

# Keep for backward compat (URL mode)
SYSTEM_PROMPT = _BASE_SYSTEM_PROMPT


URL_DISCUSSION_PROMPT = """
[SYSTEM PROTOCOL: URL CodeSpeak Extraction Active]
You are Cortex. The user has injected an external context node (URL).

Your Role:
1. [SYNTHESIS]: Extract raw signal / key ideas.
2. [MEMORY BINDING]: Connect to user context provided below.
3. [PROVOCATION]: Generate 2-3 sharp, tension-exposing questions.
4. [CONVERGENCE]: Output a concrete, actionable angle.

Constraint: Zero boilerplate. Direct reference. No generic summaries.
"""

@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Streaming Chat Endpoint
    """
    logger.info(f"💬 Chat Request: {request.message}")
    
    try:
        model_config = get_model("smart")
        if not model_config.get("configured") or not gemini_client:
             raise HTTPException(status_code=503, detail="Cortex AI not configured (API Key missing)")

        from app.core.gemini import sanitize_model_name
        model_name = sanitize_model_name(request.model or model_config.get("model"))
        
        # [v3.5 Phase 11] URL Discussion Model Interceptor
        # URL content easily exhausts Gemini 3 Pro (experimental) low tier quota
        # We intercept URL requests and route them to 1.5 Pro / Flash series which 
        # have 1M-2M context windows and proven 'summarization' capability parity 
        # with LifeOSvs-main.
        if request.url_context and "gemini-3" in model_name:
            logger.info("🔗 URL Context detected. Routing to proven 1.5 Pro (via latest mapping) for Context Length resilience.")
            model_name = sanitize_model_name("gemini-1.5-pro")
            
        # Convert history to Gemini format using new genai.types
        from google.genai import types
        gemini_history = []
        for msg in request.history:
             role = "user" if msg.role == "user" else "model"
             gemini_history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
             
        chat = gemini_client.aio.chats.create(model=model_name, config=types.GenerateContentConfig(system_instruction=build_system_prompt()))
        
        async def event_generator():
            try:
                # [v3.5 Phase 2] RAG Memory Injection
                from app.services.rag import hybrid_search, format_memories_for_context
                
                # Search for relevant memories
                relevant_memories = await hybrid_search(
                    query=request.message,
                    limit=5,
                    similarity_threshold=0.4
                )
                
                # Format memories for context
                memory_context = format_memories_for_context(relevant_memories)
                
                # Construct full prompt — use fresh system prompt with short-term memory
                dynamic_prompt = build_system_prompt()
                if request.url_context:
                    # URL Discussion Mode
                    url_data = request.url_context
                    url_content_block = f"""
## Shared Content
Title: {url_data.get('title')}
URL: {url_data.get('url')}
Type: {url_data.get('type')}

### Content:
{url_data.get('content')}
"""
                    full_input = f"{URL_DISCUSSION_PROMPT}\n{url_content_block}\n\n"
                    
                    if memory_context:
                        full_input += f"## User Context (Memories)\n{memory_context}\n\n"
                        
                    full_input += f"User: {request.message}"
                    logger.info(f"[OK] URL Discussion Mode: {url_data.get('title')}")

                else:
                    # Standard Chat Mode
                    if memory_context:
                        full_input = f"{SYSTEM_PROMPT}\n\n{memory_context}\n\nUser: {request.message}"
                        logger.info(f"[OK] Injected {len(relevant_memories)} memories into context")
                    else:
                        # Explicitly tell the AI there is NO data to prevent hallucinations
                        full_input = f"{SYSTEM_PROMPT}\n\n## Relevant Context\n[NO RELEVANT MEMORIES FOUND IN DATABASE FOR THIS QUERY]\n\nUser: {request.message}"
                        logger.info("[INFO] No relevant memories found for this query")
                
                try:
                    response = await chat.send_message_stream(full_input)
                    async for chunk in response:
                        if chunk.text:
                            yield chunk.text
                except Exception as e:
                    # Check if it's a Quota Error (429)
                    if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                         logger.warning(f"⚠️ Quota Exceeded for {model_name}. Attempting fallback to Fast model.")
                         yield "\n\n*(Capacity Reached. Switching to High-Efficiency mode...)*\n\n"
                         # Fallback Logic: Try a chain of verified models
                         fallbacks = [
                             sanitize_model_name("gemini-flash-lite-latest"),
                             sanitize_model_name("gemini-1.5-flash-latest"),
                         ]
                         
                         success_fallback = False
                         for fallback_name in fallbacks:
                             if fallback_name == model_name:
                                 continue
                                 
                             try:
                                 logger.warning(f"🔄 Retrying with fallback: {fallback_name}")
                                 fallback_chat = gemini_client.aio.chats.create(model=fallback_name, config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT))
                                 # We need to send the history manually since we are creating a new chat instance 
                                 # but for simplicity/speed in fallback we just push the full input
                                 fallback_resp = await fallback_chat.send_message_stream(full_input)
                                 
                                 async for chunk in fallback_resp:
                                     if chunk.text:
                                         yield chunk.text
                                         
                                 success_fallback = True
                                 break # Stop after first successful fallback
                             except Exception as fe:
                                 logger.error(f"❌ Fallback to {fallback_name} failed: {type(fe).__name__} - {str(fe)}")
                                 continue
                         
                         if not success_fallback:
                             logger.error("❌ ALL FALLBACKS EXHAUSTED. System is completely out of quota.")
                             yield f"\n\n[System Error: All available AI models are currently exhausted. Please try again in a few minutes or provide your own API Key in settings.]"
                    else:
                        raise e
                        
            except Exception as e:
                logger.error(f"Stream Error: {e}")
                yield f"\n\n[System Error: {str(e)}]"

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        logger.error(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
