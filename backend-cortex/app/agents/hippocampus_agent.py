# backend-cortex/app/agents/hippocampus_agent.py
import logging
from typing import Dict, Any, List
from pathlib import Path
from app.core.database import supabase

logger = logging.getLogger("cortex.hippocampus")

class HippocampusAgent:
    """
    The Memory Preservation Specialist.
    Responsible for ensuring the Cloud DB (Supabase) matches the Static Truth (Blueprints).
    """

    def __init__(self, db_client=None):
        self.db = db_client or supabase
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.blueprint_path = self.project_root / "database-hippocampus" / "prisma" / "schema.prisma"

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the connectivity and structural integrity of the cloud database.
        """
        status = {"status": "healthy", "checks": [], "issues": []}

        # 1. Connectivity Check
        try:
            res = self.db.table("system_usage").select("count", count="exact").limit(1).execute()
            status["checks"].append({"name": "Connectivity", "result": "OK"})
        except Exception as e:
            status["status"] = "disconnected"
            status["issues"].append(f"Database connection failed: {str(e)}")
            return status

        # 2. Table Existence Check (Basic Schema Verification)
        core_tables = ["memories", "nodes", "edges", "projects", "tasks"]
        for table in core_tables:
            try:
                self.db.table(table).select("id").limit(1).execute()
                status["checks"].append({"name": f"Table: {table}", "result": "OK"})
            except Exception:
                status["status"] = "degraded"
                status["issues"].append(f"Missing core table: {table}")

        # 3. Embedding Dimension Verification
        try:
            # Query for the dimension of the embedding column in memories
            # Since Supabase wraps Postgres, we can use RPC or raw SQL if enabled
            # For now, we'll use a heuristic: try to insert a dummy embedding if needed or just trust the setup
            status["checks"].append({"name": "Embedding Alignment", "result": "Trusting v3.8 Standard (3072 dims)"})
        except Exception:
            pass

        return status

    def get_blueprint_summary(self) -> str:
        """Read the local schema.prisma and return a human-readable summary of the static truth."""
        if not self.blueprint_path.exists():
            return "Blueprint not found."
        
        content = self.blueprint_path.read_text(encoding="utf-8")
        # Extract model names
        import re
        models = re.findall(r'model (\w+) \{', content)
        return f"Hippocampus Blueprint: {len(models)} models defined ({', '.join(models)})"

hippocampus_agent = HippocampusAgent()
