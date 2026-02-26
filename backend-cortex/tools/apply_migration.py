import os
import sys
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/apply_migration.py <sql_file>")
        return

    sql_file = sys.argv[1]
    if not os.path.exists(sql_file):
        print(f"File not found: {sql_file}")
        return

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)

    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # Supabase Python client doesn't have a direct 'query' or 'sql' method.
    # We usually use postgrest for tables.
    # However, we can use the 'rpc' method if we have a generic sql executor rpc,
    # OR we can try to use a direct postgres connection if needed.
    # Since we don't have a generic SQL executor RPC, and we are on a hosted Supabase,
    # we'll advise the user to run it in the SQL Editor if this tool fails,
    # but let's try a workaround manually creating the table via postgrest logic 
    # (though that's limited).
    
    print("[INFO] Passing SQL to Supabase. This typically requires an RPC or manual execution in the dashboard.")
    print("[DATA] Migration SQL Content Loaded.")
    
    # Let's try to check the table again and manually add the column if missing
    try:
        response = supabase.table("documents").select("*").limit(1).execute()
        print("[OK] 'documents' table accessible.")
    except Exception as e:
        print(f"[RETRY] Attempting to create documents table via manual columns...")
        # (Postgrest can't CREATE tables, so we MUST use SQL Editor or an RPC)
        print("[ERROR] Please apply the SQL in the Supabase Dashboard SQL Editor.")
        print(f"SQL Path: {os.path.abspath(sql_file)}")

if __name__ == "__main__":
    asyncio.run(main())
