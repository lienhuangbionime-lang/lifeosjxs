
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import supabase
from app.core.time_utils import get_today_str_taipei
from app.api.v1.memories import create_memory_entry # Helper to append to diary

router = APIRouter()
logger = logging.getLogger("cortex.tasks")

# --- Models ---
class TaskUpdate(BaseModel):
    status: str # 'todo', 'done', 'archived'

class Task(BaseModel):
    id: str
    title: str
    status: str
    project_id: Optional[str]
    created_at: str

# --- Endpoints ---

@router.get("/", response_model=List[Task])
async def get_tasks(project_id: Optional[str] = None):
    """List tasks, optionally filtered by project."""
    query = supabase.table("tasks").select("*").neq("status", "archived")
    
    if project_id:
        query = query.eq("project_id", project_id)
        
    res = query.order("created_at", desc=True).execute()
    return res.data

@router.post("/{task_id}/complete")
async def complete_task(task_id: str, background_tasks: BackgroundTasks):
    """Mark a task as done and log it to today's diary."""
    
    # 1. Update Task Status
    res = supabase.table("tasks").update({"status": "done"}).eq("id", task_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = res.data[0]
    task_title = task.get("title", "Unknown Task")
    
    # 2. Append to Diary (Background Task to avoid UI delay)
    log_content = f"- [x] **Completed Task**: {task_title} (via Project Board)"
    background_tasks.add_task(create_memory_entry, content=log_content, tags=["task", "achievement"])
    
    return {"success": True, "task": task}
