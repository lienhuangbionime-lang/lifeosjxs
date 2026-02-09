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

class ProjectMerge(BaseModel):
    target_id: int

@router.patch("/{project_id}")
async def update_project(project_id: int, project: ProjectUpdate):
    supabase = get_supabase_client()
    data = {k: v for k, v in project.dict().items() if v is not None}
    
    if not data:
        return {"message": "No data to update"}

    response = supabase.table("projects").update(data).eq("id", project_id).execute()
    # Check if data property exists and is not empty to verify success, 
    # dependent on supabase-py version but generally returns the data.
    return {"message": "Project updated", "data": response.data}

@router.delete("/{project_id}")
async def delete_project(project_id: int):
    supabase = get_supabase_client()
    # Soft delete or hard delete? Let's do hard delete for now based on request
    response = supabase.table("projects").delete().eq("id", project_id).execute()
    return {"message": "Project deleted", "data": response.data}

@router.post("/{source_id}/merge")
async def merge_project(source_id: int, merge_data: ProjectMerge):
    supabase = get_supabase_client()
    target_id = merge_data.target_id
    
    # 1. Get Source and Target
    source_res = supabase.table("projects").select("*").eq("id", source_id).single().execute()
    target_res = supabase.table("projects").select("*").eq("id", target_id).single().execute()
    
    if not source_res.data or not target_res.data:
        raise HTTPException(status_code=404, detail="Project not found")
        
    source = source_res.data
    target = target_res.data
    
    # 2. Merge Logic (Simple: Move logs/tasks to target, verify Source name is added as alias/tag)
    # For now, we'll just update the target's description or logs?
    # Since we don't have a direct 'logs' table foreign key setup shown, 
    # we might just update the name to indicate merge or move data if we had it.
    # Let's assume we copy the 'meta' or 'tags'
    
    new_tags = list(set((target.get("tags") or []) + (source.get("tags") or []) + [source["name"]]))
    
    # Update Target
    supabase.table("projects").update({"tags": new_tags}).eq("id", target_id).execute()
    
    # Archive Source
    supabase.table("projects").update({"status": "archived", "name": f"{source['name']} (Merged)"}).eq("id", source_id).execute()

    return {"message": f"Merged {source['name']} into {target['name']}"}
