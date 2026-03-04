import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("c:/Users/lien.huang/AppData/lifeosjxs/backend-cortex/.env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

async def run_test():
    try:
        # Check documents
        res = supabase.table("documents").select("id, title, url").execute()
        print("Documents in DB:", len(res.data))
        for d in res.data:
            print(f"- {d.get('title')} ({d.get('url')})")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(run_test())
