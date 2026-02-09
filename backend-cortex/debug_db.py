
import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    print("Error: Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

supabase = create_client(url, key)

async def test_insert():
    print("--- Testing Project Insertion ---")
    
    # Test 1: Minimal Insert (Name only)
    print("\n1. Trying minimal insert (name only)...")
    try:
        data = {"name": "Debug Project Minimal", "status": "idea", "progress": 0}
        res = supabase.table("Project").insert(data).execute()
        print("   SUCCESS! Created:", res.data[0]['id'])
        # Cleanup
        supabase.table("Project").delete().eq("id", res.data[0]['id']).execute()
    except Exception as e:
        print("   FAILED:", e)

    # Test 2: Full Insert (With Category)
    print("\n2. Trying full insert (with category='macro')...")
    try:
        data = {
            "name": "Debug Project Full", 
            "status": "idea", 
            "progress": 0,
            "category": "macro",
            "meta": {"emoji": "🐛"}
        }
        res = supabase.table("Project").insert(data).execute()
        print("   SUCCESS! Created:", res.data[0]['id'])
        # Cleanup
        supabase.table("Project").delete().eq("id", res.data[0]['id']).execute()
    except Exception as e:
        print("   FAILED:", e)
        print("   (This likely means the 'category' column is missing in Supabase)")

if __name__ == "__main__":
    asyncio.run(test_insert())
