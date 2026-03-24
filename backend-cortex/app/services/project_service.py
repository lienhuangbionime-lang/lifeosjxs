# [v6.0] Project Orchestration Service
from fastapi import Request
from app.core.database import get_request_client
import logging

logger = logging.getLogger("cortex.projects.service")

async def sync_project_progress(project_id: str, request: Request):
    """
    [v6.0] Recalculate project progress based on descendant task states.
    Weights: todo=0, in_progress=0.5, done=1
    """
    db = get_request_client(request)
    if not db:
        logger.warning(f"No DB client available for project sync: {project_id}")
        return
    
    try:
        # 1. Fetch all tasks for this project
        tasks_res = db.table("tasks").select("status").eq("project_id", project_id).execute()
        tasks = tasks_res.data or []
        
        if not tasks:
            # If no tasks, we don't force it to 0 yet, as it might be an empty project
            return
        
        # 2. Calculate Ratio
        total = len(tasks)
        weights = {"todo": 0, "in_progress": 0.5, "done": 1, "completed": 1}
        score = sum(weights.get(t.get("status"), 0) for t in tasks)
        
        new_progress = int((score / total) * 100)
        
        # 3. Update Project
        db.table("projects").update({"progress": new_progress}).eq("id", project_id).execute()
        logger.info(f"Project {project_id} progress synced: {new_progress}%")
        
    except Exception as e:
        logger.error(f"Failed to sync project progress for {project_id}: {e}")
