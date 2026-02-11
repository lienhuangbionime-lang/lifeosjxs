import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("--- Detailed Node Check ---")
nodes_res = supabase.table("nodes").select("*").execute()
for n in nodes_res.data:
    print(f"[{n['type']}] {n['label']} (ID: {n['id']})")

print("\n--- Edge Check ---")
edges_res = supabase.table("edges").select("*").execute()
for e in edges_res.data:
    # Try to find source and target labels
    src = next((n for n in nodes_res.data if n["id"] == e["source_id"]), None)
    tgt = next((n for n in nodes_res.data if n["id"] == e["target_id"]), None)
    src_label = src["label"] if src else "MISSING"
    tgt_label = tgt["label"] if tgt else "MISSING"
    print(f"{src_label} --({e['relation']})--> {tgt_label}")
