
import asyncio
import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from app.core.database import supabase
from app.api.v1.projects import merge_project
from fastapi import Request
from unittest.mock import MagicMock

async def test_merge():
    print("=== Testing Project Merge Logic ===")
    from app.core.database import safe_write
    
    # 1. Setup Test Data
    source_name = f"Test Source {uuid.uuid4().hex[:6]}"
    target_name = f"Test Target {uuid.uuid4().hex[:6]}"
    
    print(f"Creating source project: {source_name}")
    source_res = safe_write(supabase.table("projects"), {"name": source_name, "status": "active", "meta": {"tags": ["tag1"]}}, operation_type="insert")
    source_id = source_res.data[0]["id"]
    
    print(f"Creating target project: {target_name}")
    target_res = safe_write(supabase.table("projects"), {"name": target_name, "status": "active", "meta": {"tags": ["tag2"]}}, operation_type="insert")
    target_id = target_res.data[0]["id"]
    
    print(f"Adding task to source project...")
    task_res = safe_write(supabase.table("tasks"), {"title": "Merge Test Task", "project_id": source_id, "status": "todo"}, operation_type="insert")
    task_id = task_res.data[0]["id"]
    
    # 2. Mock DB/Request for the function
    from app.api.v1.projects import ProjectMerge
    merge_data = ProjectMerge(target_id=target_id)
    
    mock_request = MagicMock()
    mock_request.headers = {
        "X-Supabase-URL": os.getenv("SUPABASE_URL"),
        "X-Supabase-Key": os.getenv("SUPABASE_KEY")
    }
    mock_request.state.supabase_client = supabase
    
    # 3. Call Merge Function
    print(f"Executing merge: {source_id} -> {target_id}")
    try:
        # Correct order: (source_id, merge_data, request)
        result = await merge_project(source_id, merge_data, mock_request)
        print(f"Result: {result}")
        
        # 4. Verification
        print("\n--- Verifying Results ---")
        
        # Check Source Archived
        archived_src = supabase.table("projects").select("status, name").eq("id", source_id).execute()
        print(f"Source Status: {archived_src.data[0]['status']} (Expected: archived)")
        
        # Check Target Tags
        target_proj = supabase.table("projects").select("tags").eq("id", target_id).execute()
        print(f"Target Tags: {target_proj.data[0]['tags']} (Expected to include 'tag1', 'tag2', '{source_name}')")
        
        # Check Task Migrated
        migrated_task = supabase.table("tasks").select("project_id").eq("id", task_id).execute()
        print(f"Task Project ID: {migrated_task.data[0]['project_id']} (Expected: {target_id})")
        
        if migrated_task.data[0]['project_id'] == target_id:
            print("\n✅ SUCCESS: Project merge completed correctly.")
        else:
            print("\n❌ FAILURE: Task was not migrated.")
            
    except Exception as e:
        print(f"❌ ERROR during merge: {e}")
    finally:
        # 5. Cleanup (Optional but good for repetitive tests)
        # supabase.table("tasks").delete().eq("id", task_id).execute()
        # supabase.table("projects").delete().in_("id", [source_id, target_id]).execute()
        pass

if __name__ == "__main__":
    asyncio.run(test_merge())
