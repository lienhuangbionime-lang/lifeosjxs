import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

today = "2026-02-12"
print(f"Force clearing records for {today} to unblock ingestion...")

try:
    # 1. Delete Memories
    res1 = supabase.table("memories").delete().eq("date", today).execute()
    print(f"Deleted {len(res1.data)} memories.")
    
    # 2. Delete Node (Edges will cascade)
    res2 = supabase.table("nodes").delete().eq("label", today).execute()
    print(f"Deleted {len(res2.data)} nodes.")
    
    print("Cleanup successful. Your database is now ready for a fresh 3072-dim ingest.")
except Exception as e:
    print(f"Cleanup failed: {e}")
