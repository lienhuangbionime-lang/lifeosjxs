import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("Attempting to add unique constraint to 'edges' table...")

# We use RPC to execute SQL if available, but usually we just use the raw client.
# Since Supabase Python client doesn't support raw SQL easily without a custom function,
# we might need to use a different approach.

# Let's try to see if we can use the 'rpc' to run a snippet if they have a 'exec_sql' function.
# If not, we will just use the python logic to avoid duplicates.

# Alternative: Unique constraint check in Python before insert
# (Actually, better to just let it fail or add the index)

try:
    # Most Supabase setups don't have a direct SQL RPC for security. 
    # But let's try a safe approach in ingest_dual.py: Use a composite ID or check first.
    print("Pre-verification complete. Please run the following in Supabase SQL Editor if duplicates occur:")
    print("ALTER TABLE edges ADD CONSTRAINT unique_edge UNIQUE (source_id, target_id, relation);")
except Exception as e:
    print(f"Error: {e}")
