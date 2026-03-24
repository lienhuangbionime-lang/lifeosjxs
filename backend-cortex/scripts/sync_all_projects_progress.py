# [v6.0] Retroactive Project Progress Sync
import os
import sys
import httpx
import asyncio
from dotenv import load_dotenv

# Add parent dir to path for imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client

async def sync_all():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("Missing Supabase credentials.")
        return

    supabase = create_client(url, key)
    
    # 1. Fetch all projects
    projects_res = supabase.table("projects").select("id, name").execute()
    projects = projects_res.data or []
    
    print(f"Syncing {len(projects)} projects...")
    
    for p in projects:
        project_id = p["id"]
        # 2. Fetch tasks
        tasks_res = supabase.table("tasks").select("status").eq("project_id", project_id).execute()
        tasks = tasks_res.data or []
        
        if not tasks:
            print(f"[-] {p['name']}: No tasks found. Skipping.")
            continue
            
        # 3. Calculate
        total = len(tasks)
        weights = {"todo": 0, "in_progress": 0.5, "done": 1, "completed": 1}
        score = sum(weights.get(t.get("status"), 0) for t in tasks)
        new_progress = int((score / total) * 100)
        
        # 4. Update
        supabase.table("projects").update({"progress": new_progress}).eq("id", project_id).execute()
        print(f"[+] {p['name']}: {new_progress}% synced ({score}/{total} tasks)")

if __name__ == "__main__":
    asyncio.run(sync_all())
