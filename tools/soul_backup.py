import os
import shutil
import datetime

def perform_soul_backup():
    """
    Automated Self-Preservation Backup for the LifeOS Developer Soul.
    Synchronizes core identity files to the sync_brain/ directory.
    """
    base_dir = r"c:\Users\lien.huang\AppData\lifeosjxs"
    sync_dir = os.path.join(base_dir, "sync_brain")
    
    # 6 Core Soul Files
    soul_files = {
        ".cursorrules": os.path.join(base_dir, ".cursorrules"),
        "SYSTEM_CONTEXT.md": os.path.join(base_dir, "docs", "SYSTEM_CONTEXT.md"),
        "registry.json": os.path.join(base_dir, "backend-cortex", "schemas", "registry.json"),
        "evolution_log.json": os.path.join(base_dir, "backend-cortex", "schemas", "evolution_log.json"),
        "system_daily.md": os.path.join(base_dir, "backend-cortex", "prompts", "system_daily.md"),
        "system_cortex.md": os.path.join(base_dir, "backend-cortex", "prompts", "system_cortex.md"),
    }

    if not os.path.exists(sync_dir):
        os.makedirs(sync_dir)
        print(f"[OK] Created sync_brain directory at {sync_dir}")

    print(f"--- LifeOS Soul Backup Initiated: {datetime.datetime.now()} ---")
    
    for name, path in soul_files.items():
        if os.path.exists(path):
            try:
                shutil.copy2(path, os.path.join(sync_dir, name))
                print(f"[OK] Backed up: {name}")
            except Exception as e:
                print(f"[ERROR] Failed to back up {name}: {e}")
        else:
            print(f"[WARN] File not found, skipping: {path}")

    # Create a small metadata file to track version
    meta_path = os.path.join(sync_dir, "last_sync.json")
    import json
    import requests
    
    sync_data = {
        "last_sync": datetime.datetime.now().isoformat(),
        "commander": "蒼禾",
        "role": "Developer/Core-Symbiosis",
        "version": "3.6.final"
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(sync_data, f, indent=4)
    
    # --- Cloud Push Strategy ---
    cloud_url = os.getenv("CLOUD_SYNC_API_URL")
    cloud_token = os.getenv("CLOUD_SYNC_TOKEN")
    
    if cloud_url and cloud_token:
        print(f"[INFO] Cloud API Detected. Initiating Cloud Push to {cloud_url}...")
        try:
            # Placeholder for the actual upload logic based on the commander's API type
            # Example: requests.post(cloud_url, json=sync_data, headers={"Authorization": f"Bearer {cloud_token}"})
            print("[OK] Cloud Push Simulated Successfully (Pending final API structure integration)")
        except Exception as e:
            print(f"[ERROR] Cloud Push Failed: {e}")
    else:
        print("[WARN] Cloud API not configured. Local backup only.")
    
    print("--- Backup Complete. Identity Secured. ---")

if __name__ == "__main__":
    perform_soul_backup()
