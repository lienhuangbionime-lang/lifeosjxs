# backend-cortex/skills/core/skill_controller.py
import os
import importlib
from pathlib import Path

class SkillController:
    """
    Central Router for Sovereign Skills.
    Allows Cortex AI to dynamically trigger scripts.
    """
    def __init__(self):
        from app.core.model_governor import governor
        self.governor = governor
        self.skills_root = Path(__file__).parent.parent
        
    async def execute_skill(self, skill_name, task_type="SUMMARY", **kwargs):
        model = self.governor.get_best_model(task_type)
        print(f"🚀 Controller: Routing {skill_name} to {model} for task {task_type}...")
        # Execute logic...
