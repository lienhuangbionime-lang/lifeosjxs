
import asyncio
import os
from dotenv import load_dotenv
load_dotenv("C:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
from app.core.database import supabase

async def check_count():
    print("--- Database Document Count ---")
    if not supabase: return
    
    res = supabase.table("documents").select("*", count="exact").limit(1).execute()
    print(f"Total rows in 'documents': {res.count}")
    
    res_mem = supabase.table("memories").select("*", count="exact").limit(1).execute()
    print(f"Total rows in 'memories': {res_mem.count}")

if __name__ == "__main__":
    asyncio.run(check_count())
