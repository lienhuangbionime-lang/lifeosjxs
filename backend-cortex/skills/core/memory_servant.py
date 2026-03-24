import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for core imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.core.database import get_supabase_client, safe_write

logger = logging.getLogger("cortex.memory_servant")

class MemoryServant:
    """
    Manages the 'Cloud Brain' shared memory via Supabase.
    Ensures the Chat AI has instant context from a persistent Postgres table.
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table_name = "cortex_context"

    def get_current_context(self) -> dict:
        try:
            res = self.supabase.table(self.table_name).select("*").order("last_updated", desc=True).limit(1).execute()
            if res.data:
                return res.data[0]
            return {}
        except Exception as e:
            logger.warning(f"Could not fetch cloud context: {e}")
            return {}

    def update_focus(self, focus_text: str):
        payload = {
            "active_focus": focus_text,
            "last_updated": datetime.now().isoformat(),
            "status": "IDLE"
        }
        try:
            safe_write(self.supabase.table(self.table_name), payload, operation_type="upsert", on_conflict="active_focus")
            print(f"CLOUD MEMORY: Focus updated to: {focus_text}")
        except Exception as e:
            logger.error(f"Failed to update cloud memory: {e}")

    def update_status(self, status_text: str):
        """Proactive pulse of what the AI is currently doing (e.g. 'Thinking...', 'Crawling...')"""
        # We find the latest focus and update its status
        try:
            ctx = self.get_current_context()
            if not ctx: return
            
            payload = {
                "active_focus": ctx.get("active_focus"),
                "status": status_text,
                "last_updated": datetime.now().isoformat()
            }
            safe_write(self.supabase.table(self.table_name), payload, operation_type="upsert", on_conflict="active_focus")
            print(f"CLOUD PULSE: Status updated to: {status_text}")
        except Exception as e:
            logger.error(f"Failed to update cloud pulse: {e}")

if __name__ == "__main__":
    servant = MemoryServant()
    servant.update_focus("Cloud Persistence Migration (v4.7 Achievement)")
