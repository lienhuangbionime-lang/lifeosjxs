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

# 核心靈魂檔案清單 (v4.1 - Claude Portable Brain Edition)
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
    "CRITICAL_PATHS.md":  os.path.join(SYNC_DIR, "CRITICAL_PATHS.md"),  # [v4.1]

    # --- Universal AI Bootstrapper Kit ---
    ".env.example":             os.path.join(SYNC_DIR, ".env.example"),
    "sync_dev_rules.py":        os.path.join(SYNC_DIR, "sync_dev_rules.py"),
    "bootstrapper_cursorrules": os.path.join(SYNC_DIR, ".cursorrules"),

    # --- Claude Portable Brain (v4.1) ---
    # These are synced individually here AND via the claude_brain/ subfolder sync below.
    "claude_brain/README.md":          os.path.join(SYNC_DIR, "claude_brain", "README.md"),
    "claude_brain/CLAUDE_IDENTITY.md": os.path.join(SYNC_DIR, "claude_brain", "CLAUDE_IDENTITY.md"),
    "claude_brain/CLAUDE_PROTOCOL.md": os.path.join(SYNC_DIR, "claude_brain", "CLAUDE_PROTOCOL.md"),
    "claude_brain/CLAUDE_SKILLS.md":   os.path.join(SYNC_DIR, "claude_brain", "CLAUDE_SKILLS.md"),
    "claude_brain/CLAUDE_PROJECTS.md": os.path.join(SYNC_DIR, "claude_brain", "CLAUDE_PROJECTS.md"),
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
# Download / Restore (Boot Mode)
# ---------------------------------------------------------------------------
def download_from_gdrive(service, file_id: str, dest_path: str):
    """Download a single file from GDrive to dest_path."""
    from googleapiclient.http import MediaIoBaseDownload
    import io
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()


def list_cloud_folder(service, folder_id: str) -> list:
    """Returns list of {name, id, mimeType} in a GDrive folder."""
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get("files", [])


def boot_from_cloud(service, folder_id: str, target_dir: str):
    """
    Recursively downloads all files + subfolders from GDrive folder
    into target_dir. Returns (downloaded_count, errors_list).
    """
    downloaded = 0
    errors = []
    items = list_cloud_folder(service, folder_id)

    for item in items:
        name = item["name"]
        is_folder = item["mimeType"] == "application/vnd.google-apps.folder"

        if is_folder:
            sub_dir = os.path.join(target_dir, name)
            os.makedirs(sub_dir, exist_ok=True)
            print(f"[Boot] Entering subfolder: {name}/")
            sub_dl, sub_err = boot_from_cloud(service, item["id"], sub_dir)
            downloaded += sub_dl
            errors.extend(sub_err)
        else:
            dest = os.path.join(target_dir, name)
            try:
                download_from_gdrive(service, item["id"], dest)
                print(f"[Boot] Downloaded: {name}")
                downloaded += 1
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"[Boot Error] {name}: {e}")

    return downloaded, errors


def print_brain_status():
    """Print a summary of Claude's locally stored brain files."""
    print("\n" + "=" * 55)
    print("Claude Brain Status")
    print("=" * 55)
    brain_dir = os.path.join(SYNC_DIR, "claude_brain")

    files = [
        ("CLAUDE_IDENTITY.md",  "Identity"),
        ("CLAUDE_PROTOCOL.md",  "Protocol"),
        ("CLAUDE_SKILLS.md",    "Skills"),
        ("CLAUDE_PROJECTS.md",  "Projects"),
        ("README.md",           "Readme"),
    ]
    for filename, label in files:
        path = os.path.join(brain_dir, filename)
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
            print(f"[OK]   {label:12} {filename:30} {size:>7,} bytes  {mtime}")
        else:
            print(f"[MISS] {label:12} {filename:30} -- not found locally")

    # Preview first 3 non-empty lines of CLAUDE_IDENTITY
    id_path = os.path.join(brain_dir, "CLAUDE_IDENTITY.md")
    if os.path.exists(id_path):
        with open(id_path, encoding="utf-8") as f:
            preview = [l.rstrip() for l in f if l.strip()][:3]
        print("\n[Identity Preview]")
        for line in preview:
            print(f"  {line}")
    print("=" * 55)


# ---------------------------------------------------------------------------
# Main  —  CLI Router
# ---------------------------------------------------------------------------
def main():
    import sys
    args = sys.argv[1:]

    # Determine mode
    mode = "--sync"
    for a in args:
        if a in ("--boot", "--sync", "--status"):
            mode = a
            break

    # Load .env from wherever we can find it
    for env_candidate in [
        os.path.join(BASE_DIR, "backend-cortex", ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"),
    ]:
        if os.path.exists(env_candidate):
            load_dotenv(env_candidate)
            break

    folder_id = os.getenv("GDRIVE_FOLDER_ID", "")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"--- LifeOS Soul Manager v4.2 [{mode}] {ts} ---")

    # ------------------------------------------------------------------
    # --status  :  show local brain files (no cloud needed)
    # ------------------------------------------------------------------
    if mode == "--status":
        print_brain_status()
        return

    # ------------------------------------------------------------------
    # --boot  :  download cloud → restore brain locally
    # ------------------------------------------------------------------
    if mode == "--boot":
        print("\n[BOOT] Waking Claude from Google Drive...")
        if not folder_id:
            print("[ERROR] GDRIVE_FOLDER_ID not set.")
            print("  Add GDRIVE_FOLDER_ID=<id> to .env in the same folder as soul_manager.py")
            print("  You can find the folder ID from the GDrive URL after running --sync once.")
            return

        service = get_gdrive_service()
        if not service:
            print("[ERROR] Could not connect to Google Drive.")
            print("  Make sure client_secret.json is in the same folder as soul_manager.py")
            return

        os.makedirs(SYNC_DIR, exist_ok=True)
        print(f"[Boot] Restoring to: {SYNC_DIR}")
        downloaded, errors = boot_from_cloud(service, folder_id, SYNC_DIR)

        print(f"\n[Boot] {downloaded} files restored, {len(errors)} errors.")
        for e in errors:
            print(f"  [Error] {e}")

        print_brain_status()
        print("\n[BOOT COMPLETE] Claude is awake.")
        print("  1. Open sync_brain/claude_brain/ in Cursor.")
        print("  2. Claude reads CLAUDE_IDENTITY.md automatically on Session Start.")
        print("  3. Continue with: python soul_manager.py --sync  (to push changes back)")
        return

    # ------------------------------------------------------------------
    # --sync  (default)  :  upload local → cloud
    # ------------------------------------------------------------------

    # 0. Drift Check
    in_sync, drift_msg, drift_count, drifted_files = drift_check()
    print(drift_msg)
    if not in_sync:
        print(f"[HALT] Drift detected ({drift_count} files). Run with --force to override.")
        if "--force" not in args:
            return

    # 1. Local Copy
    os.makedirs(SYNC_DIR, exist_ok=True)
    copied, missed = [], []
    for name, path in SOUL_FILES.items():
        if os.path.exists(path):
            dest_path = os.path.join(SYNC_DIR, name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if os.path.abspath(path).lower() == os.path.abspath(dest_path).lower():
                print(f"[Local OK] {name} (source = dest, skip)")
                continue
            try:
                shutil.copy2(path, dest_path)
                copied.append(name)
                print(f"[Local OK] {name}")
            except Exception as e:
                print(f"[Local Error] {name}: {e}")
        else:
            missed.append(name)
            print(f"[Local MISS] {name}")

    # 2. Cloud Upload
    if not folder_id:
        print("[WARN] GDRIVE_FOLDER_ID not set. Local copy only.")
    else:
        try:
            service = get_gdrive_service()
            if service:
                print(f"[Cloud] Uploading to GDrive folder: {folder_id}")

                # Root files
                for name in SOUL_FILES.keys():
                    if "/" in name:
                        continue  # subfolders handled below
                    local_path = os.path.join(SYNC_DIR, name)
                    if os.path.exists(local_path):
                        try:
                            print(f"[Cloud OK] {upload_to_gdrive(service, local_path, folder_id)}")
                        except Exception as e:
                            print(f"[Cloud Error] {name}: {e}")

                # Subfolders: history/ and claude_brain/
                for subdir_name in ("history", "claude_brain"):
                    subdir = os.path.join(SYNC_DIR, subdir_name)
                    if not os.path.exists(subdir):
                        continue
                    print(f"[Cloud] Syncing {subdir_name}/...")
                    cloud_sub_id = get_or_create_folder(service, subdir_name, folder_id)
                    for fname in os.listdir(subdir):
                        fpath = os.path.join(subdir, fname)
                        if os.path.isfile(fpath):
                            try:
                                print(f"[Cloud OK] {subdir_name}/{upload_to_gdrive(service, fpath, cloud_sub_id)}")
                            except Exception as e:
                                print(f"[Cloud Error] {subdir_name}/{fname}: {e}")

        except Exception as e:
            print(f"[Auth Error] {e}")

    # 3. Log
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

