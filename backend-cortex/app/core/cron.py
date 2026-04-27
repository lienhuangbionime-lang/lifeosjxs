import asyncio
import os
import json
import logging
from datetime import datetime
import httpx
from app.services.rag_service import rag_service
from app.core.gemini import gemma_client, types

logger = logging.getLogger("cortex.cron")

async def cron_watcher():
    cron_dir = os.path.expanduser(r"~\.hermes\cron")
    os.makedirs(cron_dir, exist_ok=True)
    
    logger.info("?? [Cron Watcher] Started monitoring ~/.hermes/cron")
    
    while True:
        try:
            now = datetime.now()
            files = [f for f in os.listdir(cron_dir) if f.endswith(".json")]
            for filename in files:
                filepath = os.path.join(cron_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                        
                    scheduled_at = datetime.fromisoformat(payload["scheduled_at"])
                    if now >= scheduled_at:
                        if payload.get("is_subagent"):
                            logger.info(f"?? [Cron Watcher] Running autonomous subagent mission: {payload['goal']}")
                            
                            # 1. Load Protocol
                            protocol_path = os.path.join(os.getcwd(), "prompts", "subagent_protocol.md")
                            protocol = "You are a specialized AI assistant."
                            if os.path.exists(protocol_path):
                                with open(protocol_path, "r", encoding="utf-8") as pf:
                                    protocol = pf.read()
                            
                            # 2. Run Reasoning Loop
                            worker_input = f"{protocol}\n\nMISSION:\n{payload['goal']}\n\nCONTEXT:\n{payload.get('context', '')}"
                            
                            try:
                                response = await gemma_client.aio.models.generate_content(
                                    model="models/gemma-2.0-flash", # Use fast model for background tasks
                                    contents=worker_input,
                                    config=types.GenerateContentConfig(temperature=0.7, top_p=0.9)
                                )
                                result_text = response.text or "[Empty Response]"
                                
                                # 3. Archive to Supabase
                                await rag_service.ingest_text(
                                    text=result_text,
                                    meta={
                                        "source": "cron_subagent",
                                        "mission": payload["goal"],
                                        "scheduled_at": payload["scheduled_at"],
                                        "task_id": payload.get("task_id")
                                    },
                                    target="memories"
                                )
                                logger.info(f"??[Cron Watcher] Subagent mission archived to Supabase.")
                            except Exception as ai_e:
                                logger.error(f"??[Cron Watcher] Subagent AI failure: {ai_e}")
                        else:
                            logger.info(f"?? [Cron Watcher] Triggering scheduled action: {payload['intent']}")
                            
                            # Trigger the action asynchronously to the local chat endpoint
                            async with httpx.AsyncClient() as client:
                                await client.post("http://localhost:8000/api/v1/chat/message", json={
                                    "message": f"[SYSTEM AUTOMATED CRON ACTION START]\nIntent: {payload['intent']}\n[Execute this intent immediately. Take necessary actions silently.]",
                                    "model": "models/gemma-2.0-flash",
                                    "history": [],
                                    "platform": "cron"
                                }, timeout=300.0)
                            
                        # Delete the file after triggering
                        os.remove(filepath)
                        logger.info(f"??[Cron Watcher] Task {filename} executed and removed.")
                except Exception as e:
                    logger.error(f"Error processing cron file {filename}: {e}")
        except Exception as e:
            logger.error(f"Cron watcher loop error: {e}")
            
        await asyncio.sleep(30)
