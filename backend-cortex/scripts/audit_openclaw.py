import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

def audit():
    if not url or not key:
        print("Error: Supabase config missing")
        return
    
    db = create_client(url, key)
    
    print("Searching for 'OpenClaw' projects...")
    try:
        proj_res = db.table("projects").select("*").ilike("name", "%OpenClaw%").execute()
        if not proj_res.data:
            print("No matching projects found.")
        for p in proj_res.data:
            print(f"Project: {p.get('name')} | Desc: {p.get('description')}")
            print(f"Meta: {p.get('metadata')}")
            print("=" * 30)
    except Exception as e:
        print(f"Project Error: {e}")

    print("Searching for 'OpenClaw' memories...")
    try:
        res = db.table("memories").select("content,date,tags").ilike("content", "%OpenClaw%").order("date", desc=True).limit(20).execute()
        if not res.data:
            print("No matching memories found.")
        for m in res.data:
            print(f"[{m['date']}] (Tags: {m['tags']}) {m['content'][:200]}...")
            print("-" * 20)
    except Exception as e:
        print(f"Memory Error: {e}")

if __name__ == "__main__":
    audit()
