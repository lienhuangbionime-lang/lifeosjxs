import asyncio
import logging
import json
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from app.core.gemini import get_model, gemma_client, sanitize_model_name
from app.core.database import supabase
from app.core.time_utils import get_current_iso_taipei

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cortex.micro_sync")

# Constants
SYNC_BRAIN_DIR = Path(r"C:\Users\lien.huang\AppData\lifeosjxs\sync_brain")
EVOLUTION_LOG = SYNC_BRAIN_DIR / "evolution_log.json"
CORTEX_STATE = SYNC_BRAIN_DIR / "cortex_state.md"
LOOP_INTERVAL_SECONDS = 3 * 3600  # 3 Hours for standard micro-sync
SHUTDOWN_WINDOW_SECONDS = 15 * 60  # 15 Minutes for final crystallization

class MicroSyncWorker:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.last_sync_time = datetime.now(timezone.utc)
        self.model_name = sanitize_model_name("gemma-2.0-flash-lite")
        
    def setup_signal_handlers(self):
        """Register signal handlers for graceful shutdown."""
        # Windows supports SIGINT and SIGTERM
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._handle_signal)
            except Exception as e:
                logger.warning(f"Could not register handler for {sig}: {e}")

    def _handle_signal(self, sig, frame):
        logger.info(f"?ö® Shutdown signal ({sig}) received. Initiating 15-minute handover protocol...")
        self.shutdown_event.set()

    async def fetch_recent_data(self, hours: int = 3) -> str:
        """Fetch growth logs and memories from the last N hours."""
        since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        
        # 1. Fetch Growth Logs
        growth_data = []
        if supabase:
            try:
                growth_res = supabase.table("cortex_growth_logs").select("*").gte("created_at", since).execute()
                growth_data = growth_res.data or []
            except Exception as e:
                logger.warning(f"Failed to fetch growth logs: {e}")
        
        # 2. Fetch Memories
        mem_data = []
        if supabase:
            try:
                mem_res = supabase.table("memories").select("content, ai_insights").gte("created_at", since).execute()
                mem_data = mem_res.data or []
            except Exception as e:
                logger.warning(f"Failed to fetch memories: {e}")
        
        context = "=== RECENT GROWTH LOGS ===\n"
        for log in growth_data:
            context += f"- Decision: {log.get('decision_context')} -> User Choice: {log.get('user_choice')}\n"
            
        context += "\n=== RECENT MEMORIES ===\n"
        for m in mem_data:
            context += f"- {m.get('content') or m.get('ai_insights')}\n"
            
        return context

    async def crystallize_and_persist(self, mode: str = "periodic"):
        """Use Gemma to crystallize findings and update the brain."""
        logger.info(f"[Crystallizing] Mode: {mode}...")
        
        context = await self.fetch_recent_data(hours=3 if mode == "periodic" else 12)
        if not context.strip():
            logger.info("Nothing to crystallize. Skipping.")
            return

        prompt = f"""You are the Micro-Sync Engine (v4.6).
Analyze the following recent session data and extract ONLY:
1. Finalized Decisions (Strategic commitments).
2. Architectural Shifts (Changes to code or system logic).
3. Critical Lessons Learned.

=== DATA ===
{context}

=== DIRECTIVE ===
- Mode: {mode.upper()}
- Output: A JSON object:
{{
  "decisions": ["..."],
  "architecture_shifts": ["..."],
  "summary": "3 brief sentences describing the session state."
}}
- Language: Traditional Chinese (ÁπÅÈ?‰∏≠Ê?).
"""
        if not gemma_client:
            logger.warning("gemma_client is None. Skipping LLM crystallization.")
            return

        try:
            from app.core.gemini import safe_generate_content
            response = await safe_generate_content(
                client=gemma_client,
                prefer_mode="fast",
                contents=prompt,
                config={"temperature": 0.2, "response_mime_type": "application/json"}
            )
            
            data = json.loads(response.text.strip())
            
            # 1. Append to evolution_log.json
            if data.get("decisions") or data.get("architecture_shifts"):
                self._append_to_evolution_log(data, mode)
                
            # 2. Update CORTEX_STATE.md Next Steps if in SHUTDOWN mode
            if mode == "shutdown":
                self._update_cortex_state(data["summary"])
                
            logger.info(f"??Micro-Sync success. Mode: {mode}")
            
        except Exception as e:
            logger.error(f"Crystallization failed: {e}")

    def _append_to_evolution_log(self, data: dict, mode: str):
        if not EVOLUTION_LOG.exists():
             EVOLUTION_LOG.write_text("[]", encoding="utf-8")
             
        try:
            with open(EVOLUTION_LOG, "r+", encoding="utf-8") as f:
                logs = json.load(f)
                logs.append({
                    "timestamp": get_current_iso_taipei(),
                    "event": f"micro_sync_{mode}",
                    "type": "MICRO_SYNC",
                    "description": data["summary"],
                    "meta": {
                        "decisions": data.get("decisions", []),
                        "shifts": data.get("architecture_shifts", [])
                    }
                })
                f.seek(0)
                json.dump(logs, f, ensure_ascii=False, indent=2)
                f.truncate()
        except Exception as e:
            logger.error(f"Failed to write to evolution log: {e}")

    def _update_cortex_state(self, summary: str):
        """Update the 'Next Steps' in cortex_state.md to preserve handover context."""
        if not CORTEX_STATE.exists(): return
        content = CORTEX_STATE.read_text(encoding="utf-8")
        
        # Replace the 'Next Step' line or append a 'Handover' section
        new_next_step = f"- **Next Step (Handover)**: {summary}"
        import re
        content = re.sub(r"- \*\*Next Step\*\*: .*", new_next_step, content)
        
        CORTEX_STATE.write_text(content, encoding="utf-8")
        logger.info("Brain updated with shutdown handover context.")

    async def start(self):
        """Main Loop."""
        logger.info("?? Micro-Sync Worker starting in CONTINUOUS mode...")
        self.setup_signal_handlers()
        
        while not self.shutdown_event.is_set():
            await self.crystallize_and_persist(mode="periodic")
            
            # Use wait with timeout to check for shutdown_event frequently
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=LOOP_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                continue # Normal loop
                
        # --- SHUTDOWN HANDOVER PROTOCOL ---
        logger.info("??EXECUTION HANDOVER: Starting final 15-minute crystallization...")
        await self.crystallize_and_persist(mode="shutdown")
        logger.info("?í§ Micro-Sync Worker entering dormancy. System sync complete.")

if __name__ == "__main__":
    from datetime import timedelta # Missing import for fetch_recent_data
    worker = MicroSyncWorker()
    asyncio.run(worker.start())
