from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.core.database import get_supabase_client

router = APIRouter()

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None

class ProjectCreate(BaseModel):
    name: str
    category: str = "macro"
    status: str = "active"
    progress: int = 0
    meta: Optional[Dict[str, Any]] = {}
    
class ProjectMerge(BaseModel):
    target_id: str

@router.post("/")
async def create_project(project: ProjectCreate):
    supabase = get_supabase_client()
    try:
        data = project.dict()

        # [FIX] Handle missing 'category' column in DB
        # Move 'category' to 'meta' 
        if "category" in data:
            if "meta" not in data or data["meta"] is None:
                data["meta"] = {}
            data["meta"]["category"] = data.pop("category")
        
        response = supabase.table("projects").insert(data).execute()
        return {"message": "Project created", "data": response.data}
    except Exception as e:
        import logging
        logger = logging.getLogger("cortex.projects")
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{project_id}")
async def update_project(project_id: str, project: ProjectUpdate):
    supabase = get_supabase_client()
    data = {k: v for k, v in project.dict().items() if v is not None}
    
    if not data:
        return {"message": "No data to update"}

    # [FIX] Handle missing 'category' column (if update tries to set it, though ProjectUpdate doesn't have it yet)
    # ProjectUpdate model doesn't have category, so this is safe for now.
    
    response = supabase.table("projects").update(data).eq("id", project_id).execute()
    return {"message": "Project updated", "data": response.data}

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    supabase = get_supabase_client()
    response = supabase.table("projects").delete().eq("id", project_id).execute()
    return {"message": "Project deleted", "data": response.data}

@router.post("/{source_id}/merge")
async def merge_project(source_id: str, merge_data: ProjectMerge):
    supabase = get_supabase_client()
    target_id = merge_data.target_id
    
    # 1. Get Source and Target
    source_res = supabase.table("projects").select("*").eq("id", source_id).single().execute()
    target_res = supabase.table("projects").select("*").eq("id", target_id).single().execute()
    
    if not source_res.data or not target_res.data:
        raise HTTPException(status_code=404, detail="Project not found")
        
    source = source_res.data
    target = target_res.data
    
    # 2. Merge Logic
    new_tags = list(set((target.get("tags") or []) + (source.get("tags") or []) + [source["name"]]))
    
    # Update Target
    supabase.table("projects").update({"tags": new_tags}).eq("id", target_id).execute()
    
    # Archive Source
    supabase.table("projects").update({"status": "archived", "name": f"{source['name']} (Merged)"}).eq("id", source_id).execute()

    return {"message": f"Merged {source['name']} into {target['name']}"}
