import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("cortex.security")

class IntentValidator:
    """
    [Sovereign Autonomy Protocol: Zero-Trust Defense]
    Semantic Firewall to validate dangerous intents against recent conversation context.
    """
    
    DANGEROUS_INTENTS = ["DELETE", "RESET", "RELOAD_CORE", "WIPE_MEMORIES"]
    
    def __init__(self, db):
        self.db = db
        self.hot_memory_path = Path(r"c:\Users\lien.huang\AppData\lifeosjxs\sync_brain\cortex_state.md")
        if not self.hot_memory_path.exists():
            self.hot_memory_path = Path("sync_brain/cortex_state.md")

    async def validate_intent(self, intent: str, action_summary: str, user_id: str = "Lien") -> Dict[str, Any]:
        """
        Validates if the current destructive intent matches the recent conversation context.
        """
        if intent not in self.DANGEROUS_INTENTS:
            return {"valid": True, "reason": "Non-destructive intent."}
        
        logger.warning(f"?›¡ï¸?[SECURITY] Destructive Intent Detected: {intent} - {action_summary}")
        
        # 1. Fetch last 2 hours of memories (Context Check)
        two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        context_verified = False
        justification_found = ""
        
        if self.db:
            try:
                # Query memories created in the last 2 hours
                res = self.db.table("memories").select("content").gt("created_at", two_hours_ago).execute()
                recent_memories = res.data or []
                
                # Check if any memory contains words related to the action
                # In a more advanced version, we'd use a small model to verify the match
                action_keywords = action_summary.lower().split()
                for mem in recent_memories:
                    content = mem.get("content", "").lower()
                    if any(kw in content for kw in action_keywords):
                        context_verified = True
                        justification_found = content[:100] + "..."
                        break
            except Exception as e:
                logger.error(f"[SECURITY ERROR] Failed to fetch context for validation: {e}")
        
        if context_verified:
            logger.info(f"?›¡ï¸?[SECURITY] Intent Validated by Context: {justification_found}")
            return {"valid": True, "reason": "Contextual justification found."}
        else:
            logger.error(f"?š¨ [SECURITY] CONTEXT MISMATCH! No justification found for {intent}.")
            return {
                "valid": False,
                "reason": "Context Mismatch: No recent discussion found about this destructive action.",
                "action_required": "EMERGENCY_HANG",
                "alert": f"Commander, an unauthorized {intent} was attempted without prior context. System is hanging the task."
            }

# Global instance
intent_validator = None

def get_intent_validator(db):
    global intent_validator
    if intent_validator is None:
        intent_validator = IntentValidator(db)
    return intent_validator
