
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase

async def check_tasks():
    print(f"--- Database URL: {os.getenv('SUPABASE_URL')} ---")
    if not supabase: return
    
    res = supabase.table("tasks").select("id, title").limit(5).execute()
    if res.data:
        print(f"Found {len(res.data)} tasks:")
        for t in res.data:
            print(f"- {t['title']}")
    else:
        print("Tasks table is empty.")

if __name__ == "__main__":
    asyncio.run(check_tasks())
