import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

today = "2026-02-12"
print(f"Checking records for {today}...")

res = supabase.table("memories").select("id, content, date").eq("date", today).execute()
print(f"Found {len(res.data)} records:")
for r in res.data:
    print(f"- ID: {r['id']}, Content Preview: {r['content'][:30]}...")
