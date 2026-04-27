# app/api/v1/endpoints/chat.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.rag_service import rag_service
import logging

router = APIRouter()
logger = logging.getLogger("cortex.chat")

from typing import Optional

class ChatMessage(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    session_id: Optional[str] = None

@router.post("/ingest")
async def ingest_content(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    try:
        count = 0
        if file:
            # Track usage
            from app.core.usage import track_usage
            await track_usage(1)
            count += await rag_service.ingest_file(file)
        if text:
            from app.core.usage import track_usage
            await track_usage(1)
            count += await rag_service.ingest_text(text, {"source": "manual_entry"})
            
        return {"success": True, "chunks_added": count}
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def chat_message(body: ChatMessage, request: Request):
    try:
        # Track usage
        from app.core.usage import track_usage
        await track_usage(1)
        
        async def agentic_loop():
            import asyncio
            
            # 1. System Heartbeat Direct Bypass
            if body.message.strip().lower() == "system_check":
                yield "\n[HEARTBEAT] System Cortex Active. Agentic Loop Healthy. Memory Database Connected.\n"
                return

            from app.core.gemini import get_request_gemini_client, types, get_model
            client = get_request_gemini_client(request)
            if not client:
                yield "Error: Gemini client is not configured."
                return
                
            model_info = get_model("fast")
            model_id = model_info["model"]
            
            # 2. Initialize Context History & Session Recovery
            formatted_history = []
            
            # [NEW] Session Persistence Recovery (load_session)
            if not body.history and getattr(body, "session_id", None):
                try:
                    from app.core.database import get_request_client
                    db = get_request_client(request)
                    if db and not getattr(db, "_is_guest_mode", False):
                        def fetch_session():
                            return db.table("session_states").select("history").eq("session_id", body.session_id).order("created_at", desc=True).limit(1).execute()
                        resp = await asyncio.to_thread(fetch_session)
                        
                        if getattr(resp, "data", None) and len(resp.data) > 0:
                            db_history = resp.data[0].get("history", [])
                            # Reconstruct History
                            for item in db_history:
                                parts = []
                                for part_dict in item.get("parts", []):
                                    if "text" in part_dict:
                                        parts.append(types.Part.from_text(text=part_dict["text"]))
                                    elif "function_call" in part_dict:
                                        fc_data = part_dict["function_call"]
                                        parts.append(types.Part.from_function_call(name=fc_data["name"], args=fc_data.get("args", {})))
                                    elif "function_response" in part_dict:
                                        fr_data = part_dict["function_response"]
                                        parts.append(types.Part.from_function_response(name=fr_data["name"], response=fr_data.get("response", {})))
                                formatted_history.append(types.Content(role=item.get("role"), parts=parts))
                                
                            logger.info(f"Successfully loaded session {body.session_id} with {len(formatted_history)} turns.")
                except Exception as load_e:
                    logger.warning(f"Failed to load session {body.session_id}: {load_e}")

            # Fallback to frontend history if DB load fails or is empty
            if not formatted_history:
                for msg in body.history:
                    role = "user" if msg["role"] == "user" else "model"
                    formatted_history.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg["content"])]
                    ))
                
            formatted_history.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=body.message)]
            ))
            
            # 3. Tool Schema Construction
            from app.core.cortex_tools import get_tools_schema, get_tools_map
            from app.core.database import get_request_client
            
            db = get_request_client(request)
            tools_schema = get_tools_schema()
            tools_map = get_tools_map(db) if db else {}
            
            config = types.GenerateContentConfig(
                tools=[types.Tool(function_declarations=tools_schema)],
                system_instruction="You are Cortex. Think concisely within <thought> tags before acting. Use your provided tools to archive memories, scan stocks, or manage tasks. Always prioritize long-term memory archiving via save_memory.",
                temperature=0.6
            )
            
            total_retries = 0
            total_tokens = 0
            try:
                # 4. Action Loop with Exponential Backoff
                max_steps = 5
                for step in range(max_steps):
                    response_stream = None
                    delays = [2, 4, 8]
                    
                    for attempt, delay in enumerate(delays + [0]):
                        try:
                            response_stream = await client.aio.models.generate_content_stream(
                                model=model_id,
                                contents=formatted_history,
                                config=config
                            )
                            break # Success, break out of retry loop
                        except Exception as e:
                            error_msg = str(e)
                            if any(err in error_msg for err in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]) and attempt < len(delays):
                                total_retries += 1
                                logger.warning(f"Retrying due to 429 (Attempt {attempt+1}/3)")
                                yield f"\n<thought> Connection throttled (429/503). Retrying in {delay}s... (Attempt {attempt+1}/3) </thought>\n"
                                await asyncio.sleep(delay)
                            else:
                                logger.error(f"Generation failed permanently: {e}")
                                yield f"\n**Generation Error**: {str(e)}\n"
                                return # Exit agentic loop safely

                    if not response_stream:
                        return
                        
                    function_calls = []
                    async for chunk in response_stream:
                        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                            total_tokens = getattr(chunk.usage_metadata, "total_token_count", total_tokens)
                            
                        if chunk.text:
                            yield chunk.text
                        if chunk.function_calls:
                            function_calls.extend(chunk.function_calls)
                            
                    if not function_calls:
                        # No more tools needed, loop ends
                        break
                        
                    # Execute Tools
                    formatted_history.append(types.Content(
                        role="model",
                        parts=[types.Part.from_function_call(name=fc.name, args=fc.args) for fc in function_calls]
                    ))
                    
                    function_responses = []
                    for fc in function_calls:
                        tool_name = fc.name
                        tool_args = fc.args or {}
                        yield f"\n<thought> Triggering Tool: {tool_name}({tool_args}) </thought>\n"
                        
                        try:
                            if tool_name in tools_map:
                                tool_fn = tools_map[tool_name]
                                # Handle both async and sync tools
                                if asyncio.iscoroutinefunction(tool_fn):
                                    result = await tool_fn(**tool_args)
                                else:
                                    result = tool_fn(**tool_args)
                            elif tool_name == "search_memory": # Legacy fallback
                                result_dict = await rag_service.unified_search(tool_args.get("query", ""))
                                result = result_dict.get("memories", "") + "\n" + result_dict.get("documents", "")
                            else:
                                result = f"Error: Tool '{tool_name}' not found."
                        except Exception as tool_e:
                            logger.error(f"Tool {tool_name} failed: {tool_e}")
                            result = f"Error executing {tool_name}: {tool_e}"
                            
                        function_responses.append(
                            types.Part.from_function_response(
                                name=tool_name,
                                response={"result": str(result)}
                            )
                        )
                    
                    formatted_history.append(types.Content(
                        role="user",
                        parts=function_responses
                    ))

            finally:
                # 6. Performance Metrics Audit
                logger.info(f"{{'tokens_used': {total_tokens}, 'retries': {total_retries}, 'status': 'success'}}")
                
                # 5. Session State Persistence
                def save_state(history_payload):
                    try:
                        from app.core.database import get_request_client
                        db = get_request_client(request)
                        if db and not getattr(db, "_is_guest_mode", False):
                            # Upsert to session_states so it overrides the same session ID
                            db.table("session_states").upsert(history_payload).execute()
                            logger.info(f"Agentic Loop history persisted to session_states (ID: {history_payload.get('session_id')}).")
                    except Exception as save_e:
                        logger.warning(f"Failed to persist session to Supabase: {save_e}")
                
                # Serialize history to JSON-safe dictionary
                serializable_history = []
                for item in formatted_history:
                    parts = []
                    for p in getattr(item, 'parts', []):
                        if p.text: 
                            parts.append({"text": p.text})
                        elif p.function_call: 
                            # Safe serialization of args dict
                            arg_dict = dict(p.function_call.args) if getattr(p.function_call, 'args', None) else {}
                            parts.append({"function_call": {"name": p.function_call.name, "args": arg_dict}})
                        elif p.function_response: 
                            resp_dict = dict(p.function_response.response) if getattr(p.function_response, 'response', None) else {}
                            parts.append({"function_response": {"name": p.function_response.name, "response": resp_dict}})
                    serializable_history.append({"role": item.role, "parts": parts})
                    
                import json
                import uuid
                session_id_val = getattr(body, "session_id", None)
                if not session_id_val:
                    session_id_val = f"cortex-{uuid.uuid4().hex[:8]}"

                payload = {
                    "session_id": session_id_val,
                    "last_message": body.message,
                    "history": serializable_history,
                }
                
                try:
                    # Offload to background thread so it doesn't block stream closure
                    asyncio.create_task(asyncio.to_thread(save_state, payload))
                except Exception as t_e:
                    logger.warning(f"Could not async dump session state: {t_e}")

        return StreamingResponse(
            agentic_loop(), 
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

