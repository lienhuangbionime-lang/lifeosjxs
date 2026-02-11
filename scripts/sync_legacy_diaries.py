"""
LifeOS v3.6 - Legacy Data Synchronization Tool
Usage: python scripts/sync_legacy_diaries.py <path_to_json>
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path

# Add backend to path
BACKEND_ROOT = Path(__file__).parent.parent / "backend-cortex"
sys.path.append(str(BACKEND_ROOT))

# Mock environment variables if not set for local script execution
os.environ.setdefault("SUPABASE_URL", "")
os.environ.setdefault("SUPABASE_KEY", "")
os.environ.setdefault("GEMINI_API_KEY", "")

async def migrate_json(file_path: str):
    print(f"🚀 Starting Migration: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File {file_path} not found.")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
        return

    if not isinstance(entries, list):
        print("❌ Error: JSON must be a list of entries.")
        return

    print(f"📊 Found {len(entries)} entries. Initializing bridge...")

    # Import Ingest Logic
    try:
        from routers.ingest_dual import ingest_log, IngestLogEntry
    except ImportError as e:
        print(f"❌ Error importing backend logic: {e}")
        print("Make sure you are running this from the project root and requirements are installed.")
        return

    success_count = 0
    fail_count = 0

    for idx, entry in enumerate(entries):
        content = entry.get("content", "")
        date_str = entry.get("date", "")
        
        if not content or not date_str:
            print(f"⚠️ Skipping entry {idx}: Missing content or date.")
            continue

        # Prepare Entry object
        log_entry = IngestLogEntry(
            content=content,
            mood=entry.get("mood", 5),
            focus=entry.get("focus", 5),
            energy=entry.get("energy", 5),
            tags=entry.get("tags", []),
            projects=entry.get("projects", []),
            date=date_str
        )

        print(f"[{idx+1}/{len(entries)}] Syncing {date_str}...", end="\r")
        
        try:
            # This will trigger: 
            # 1. Supabase Insert
            # 2. C Kernel Secure Write (Local)
            # 3. Vector Embedding Generation (AI Search)
            # 4. Neural Graph Linkage
            res = await ingest_log(log_entry)
            
            if res.status in ["synced", "db_only", "kernel_only"]:
                success_count += 1
            else:
                print(f"\n❌ Failed to sync {date_str}: {res.message}")
                fail_count += 1
        except Exception as e:
            print(f"\n❌ Crash on {date_str}: {e}")
            fail_count += 1

    print(f"\n\n✨ Migration Complete!")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📂 Archive backup created in data/import_archive/")
    
    # Backup the source file
    archive_name = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_path)}"
    archive_path = Path(__file__).parent.parent / "data" / "import_archive" / archive_name
    try:
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except:
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/sync_legacy_diaries.py <path_to_json>")
    else:
        asyncio.run(migrate_json(sys.argv[1]))
