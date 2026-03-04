# LifeOS Soul Manager v3.6.3
# Handles identity sync + drift detection across AI operatives.
import os
import json
import datetime
import shutil
import hashlib
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

# [2026-02-24] Phase A: Drift Detection Added.
# ---------------------------------------------------------------------------
BASE_DIR = r"c:\Users\lien.huang\AppData\lifeosjxs"
SYNC_DIR = os.path.join(BASE_DIR, "sync_brain")
TOKEN_FILE = os.path.join(BASE_DIR, "backend-cortex", "token.json")
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, "backend-cortex", "client_secret.json")
EVOLUTION_LOG = os.path.join(SYNC_DIR, "evolution_log.json")

# 核心靈魂檔案清單 (v4.0 - Agentic DNA Edition)
SOUL_FILES = {
    ".cursorrules":       os.path.join(BASE_DIR, ".cursorrules"),
    "SYSTEM_CONTEXT.md":  os.path.join(SYNC_DIR, "SYSTEM_CONTEXT.md"),
    "registry.json":      os.path.join(BASE_DIR, "backend-cortex", "schemas", "registry.json"),
    "SKILLS.md":          os.path.join(SYNC_DIR, "SKILLS.md"),
    "evolution_log.json": os.path.join(SYNC_DIR, "evolution_log.json"),
    "task.md":            os.path.join(SYNC_DIR, "task.md"),
    "ROADMAP.md":         os.path.join(SYNC_DIR, "ROADMAP.md"),
    "QUESTIONS.md":       os.path.join(SYNC_DIR, "QUESTIONS.md"),
    "START_HERE.md":      os.path.join(SYNC_DIR, "START_HERE.md"),
    
    # --- Universal AI Bootstrapper Kit ---
    ".env.example":             os.path.join(SYNC_DIR, ".env.example"),
    "sync_dev_rules.py":        os.path.join(SYNC_DIR, "sync_dev_rules.py"),
    "bootstrapper_cursorrules": os.path.join(SYNC_DIR, ".cursorrules"),
}


SCOPES = ['https://www.googleapis.com/auth/drive.file']


# ---------------------------------------------------------------------------
# [REFINED] Drift Detection (Phase C)
# ---------------------------------------------------------------------------
def drift_check():
    """
    Compares all files in SOUL_FILES with their counterparts in sync_brain.
    Returns (in_sync: bool, summary: str, drift_count: int, drifted_files: list).
    """
    drift_count = 0
    drifted_files = []

    def get_file_hash(filepath):
        if not os.path.exists(filepath):
            return None
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    for name, source_path in SOUL_FILES.items():
        dest_path = os.path.join(SYNC_DIR, name)
        
        # Skip if source and dest are the same path (already in sync_brain)
        if os.path.abspath(source_path).lower() == os.path.abspath(dest_path).lower():
            continue
            
        source_hash = get_file_hash(source_path)
        dest_hash = get_file_hash(dest_path)

        if source_hash != dest_hash:
            drift_count += 1
            drifted_files.append(name)

    if drift_count == 0:
        return True, "[OK] All soul files aligned.", 0, []
    else:
        return False, f"[DRIFT] {drift_count} files differ: {', '.join(drifted_files)}", drift_count, drifted_files


def log_evolution(event: str, event_type: str, description: str, impact: str = "Medium", meta: dict = None):
    """Append an event to evolution_log.json with optional metadata."""
    try:
        if os.path.exists(EVOLUTION_LOG):
            with open(EVOLUTION_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        else:
            log = []

        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            "type": event_type,
            "description": description,
            "impact": impact
        }
        if meta:
            entry["meta"] = meta

        log.append(entry)

        with open(EVOLUTION_LOG, "w", encoding="utf-8", newline="\n") as f:
            json.dump(log, f, indent=4, ensure_ascii=False)

        print(f"[OK] Evolution log updated: {event}")
    except Exception as e:
        print(f"[WARN] Evolution log write failed: {e}")


# ---------------------------------------------------------------------------
# Google Drive
# ---------------------------------------------------------------------------
def get_gdrive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"[ERROR] {CLIENT_SECRET_FILE} not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def upload_to_gdrive(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    # If file_path is inside a subfolder (like history/), we might want to mirror that.
    # For now, let's just use the basename to avoid complex folder creation logic
    # unless we check for the folder first.
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    
    # Handle potentially large files with MediaFileUpload
    media = MediaFileUpload(file_path, resumable=True)

    if files:
        service.files().update(fileId=files[0]['id'], media_body=media).execute()
        return f"Updated: {file_name}"
    else:
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return f"Created: {file_name}"

def get_or_create_folder(service, folder_name, parent_id):
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import sys
    env_path = os.path.join(BASE_DIR, "backend-cortex", ".env")
    load_dotenv(env_path)

    print(f"--- LifeOS Soul Sync v3.5.2 {datetime.datetime.now()} ---")

    # 0. Drift Check — halt if versions mismatch (use --force to override)
    in_sync, drift_msg, drift_count, drifted_files = drift_check()
    print(drift_msg)
    if not in_sync:
        print(f"[HALT] Evolution drift detected ({drift_count} files). Align context before syncing.")
        print("       Run with --force to override.")
        if "--force" not in sys.argv:
            return

    # 1. Local Copy
    if not os.path.exists(SYNC_DIR):
        os.makedirs(SYNC_DIR)

    copied = []
    missed = []
    for name, path in SOUL_FILES.items():
        if os.path.exists(path):
            dest_path = os.path.join(SYNC_DIR, name)
            if os.path.abspath(path).lower() == os.path.abspath(dest_path).lower():
                print(f"[Local OK] {name} (source = dest, skip copy)")
                continue
            try:
                shutil.copy2(path, dest_path)
                copied.append(name)
                print(f"[Local OK] {name}")
            except Exception as e:
                print(f"[Local Error] {name}: {e}")
        else:
            missed.append(name)
            print(f"[Local MISS] {name} at {path}")

    # 2. Cloud Sync
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        print("[WARN] GDRIVE_FOLDER_ID not set. Skipping cloud sync.")
    else:
        try:
            service = get_gdrive_service()
            if service:
                print(f"[Cloud] Syncing to Folder: {folder_id}...")
                for name in SOUL_FILES.keys():
                    local_path = os.path.join(SYNC_DIR, name)
                    if os.path.exists(local_path):
                        try:
                            msg = upload_to_gdrive(service, local_path, folder_id)
                            print(f"[Cloud OK] {msg}")
                        except Exception as e:
                            print(f"[Cloud Error] {name}: {e}")
                
                # 2.1 Sync 'history' subdirectory
                history_dir = os.path.join(SYNC_DIR, "history")
                if os.path.exists(history_dir):
                    print("[Cloud] Syncing 'history' directory...")
                    cloud_history_id = get_or_create_folder(service, "history", folder_id)
                    for h_file in os.listdir(history_dir):
                        h_path = os.path.join(history_dir, h_file)
                        if os.path.isfile(h_path):
                             try:
                                msg = upload_to_gdrive(service, h_path, cloud_history_id)
                                print(f"[Cloud OK] history/{msg}")
                             except Exception as e:
                                print(f"[Cloud Error] history/{h_file}: {e}")
        except Exception as e:
            print(f"[Auth Error] {e}")

    # 3. Log sync event with drift_count
    log_evolution(
        event="Soul Sync",
        event_type="SYNC",
        description=f"Synced {len(copied)} files. Missed: {missed}.",
        impact="Low",
        meta={
            "drift_count": drift_count,
            "drifted_files": drifted_files,
            "copied_count": len(copied),
            "missed_count": len(missed),
            "status": "in_sync" if in_sync else "drift_resolved"
        }
    )

    print("--- LifeOS Identity Secured ---")


if __name__ == "__main__":
    main()
