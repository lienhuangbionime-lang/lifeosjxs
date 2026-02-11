import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("--- LifeOS Graph Purification Initiated ---")

try:
    # Delete all edges first
    print("Deleting all edges...")
    supabase.table("edges").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    # Delete all nodes
    print("Deleting all nodes...")
    supabase.table("nodes").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    
    print("Purification Complete. Neural Graph is now empty.")
    print("Action: Please re-save your 2/1 and 2/2 entries in the UI now.")
except Exception as e:
    print(f"Purification Error: {str(e)}")
