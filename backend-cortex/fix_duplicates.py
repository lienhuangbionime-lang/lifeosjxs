import os
from supabase import create_client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("--- Supabase Deduplication Engine Starting ---")

def fix_memories():
    print("Checking for duplicate memories by date...")
    res = supabase.table("memories").select("id, date, created_at").order("created_at", desc=True).execute()
    
    date_map = defaultdict(list)
    for m in res.data:
        date_map[m["date"]].append(m["id"])
    
    deleted_count = 0
    for date, ids in date_map.items():
        if len(ids) > 1:
            # Keep the newest (first in our list), delete others
            to_delete = ids[1:]
            print(f"  Treating date {date}: Keeping {ids[0]}, deleting {len(to_delete)} duplicates")
            for tid in to_delete:
                supabase.table("memories").delete().eq("id", tid).execute()
                deleted_count += 1
    print(f"Done. Removed {deleted_count} duplicate memories.")

def fix_edges():
    print("Checking for duplicate edges...")
    res = supabase.table("edges").select("*").execute()
    
    edge_keys = set()
    to_delete_ids = []
    
    for edge in res.data:
        # Create a key: source + target + relation
        key = (edge["source_id"], edge["target_id"], edge["relation"])
        if key in edge_keys:
            to_delete_ids.append(edge["id"])
        else:
            edge_keys.add(key)
    
    if to_delete_ids:
        print(f"  Found {len(to_delete_ids)} duplicate edges.")
        # Delete in chunks to avoid URL length issues
        step = 50
        for i in range(0, len(to_delete_ids), step):
            chunk = to_delete_ids[i:i+step]
            supabase.table("edges").delete().in_("id", chunk).execute()
    print(f"Done. Removed {len(to_delete_ids)} duplicate edges.")

if __name__ == "__main__":
    try:
        fix_memories()
        fix_edges()
        print("\n✨ Database is now clean and deduplicated.")
    except Exception as e:
        print(f"Error during deduplication: {e}")
