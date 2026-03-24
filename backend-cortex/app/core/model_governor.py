# app/core/model_governor.py
import logging
from typing import Dict, Any

logger = logging.getLogger("cortex.governor")

class ModelGovernor:
    """
    Sovereign Resource Governor v1.0
    Allocates tasks based on RPM/TPM limits provided by the Commander.
    """
    
    LIMITS = {
        "gemini-flash-lite": {"rpm": 15, "tpm": 250000, "rpd": 500},
        "gemma-3-27b": {"rpm": 30, "tpm": 150000, "rpd": 14400}
    }

    # Task Affinity Mapping
    TASK_MAP = {
        "DIARY_INGEST": "gemini-flash-lite",
        "WEB_SCOUT": "gemini-flash-lite",
        "SUMMARY": "gemini-flash-lite",
        "DEEP_REASONING": "gemma-3-27b",
        "MEMORY_MERGE": "gemma-3-27b",
        "CODE_REFACTOR": "gemma-3-27b"
    }

    def get_best_model(self, task_type: str) -> str:
        model = self.TASK_MAP.get(task_type, "gemini-flash-lite")
        logger.info(f"⚖️ Governor: Routing task '{task_type}' to model '{model}'")
        return model

    def check_capacity(self, model: str) -> bool:
        # Placeholder for real-time tracking (Redis/Local DB)
        return True

governor = ModelGovernor()
