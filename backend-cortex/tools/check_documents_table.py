import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

async def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("[ERROR] Missing Supabase credentials.")
        return

    supabase: Client = create_client(url, key)
    
    try:
        # Try to select from documents to see if it exists
        response = supabase.table("documents").select("*").limit(1).execute()
        print("[OK] 'documents' table exists.")
        print("Sample data:", response.data)
        
        # Try to get column names if possible (via a dummy insert or just assuming standard)
        # Actually, let's try to run a query to information_schema if we have permissions
        query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'documents'"
        # Supabase client doesn't directly support raw SQL unless via RPC.
        # Let's try to check if there is an RPC for schema discovery.
        
    except Exception as e:
        print(f"[INFO] 'documents' table might not exist or inaccessible: {e}")

if __name__ == "__main__":
    asyncio.run(main())
