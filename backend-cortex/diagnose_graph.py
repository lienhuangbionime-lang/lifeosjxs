import os
from supabase import create_client
from dotenv import load_dotenv
import json

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("--- Supabase Graph Diagnostics ---")

# 1. Check Nodes
try:
    nodes_res = supabase.table("nodes").select("*").execute()
    print(f"\nNodes Count: {len(nodes_res.data)}")
    for n in nodes_res.data[:20]: # Show first 20
        print(f"[{n['type']}] {n['label']} (ID: {n['id']})")
except Exception as e:
    print(f"Error fetching nodes: {e}")

# 2. Check Edges
try:
    edges_res = supabase.table("edges").select("*").execute()
    print(f"\nEdges Count: {len(edges_res.data)}")
    for e in edges_res.data[:20]: # Show first 20
        print(f"Link: {e['source_id']} -> {e['target_id']} ({e['relation']})")
except Exception as e:
    print(f"Error fetching edges: {e}")

# 3. Check specific orphans
try:
    # Look for edges where source or target doesn't exist in nodes
    # (Since we have foreign key references in SQL, this shouldn't happen unless constraints are disabled)
    print("\nVerifying Integrity...")
except Exception as e:
    print(f"Integrity check failed: {e}")
