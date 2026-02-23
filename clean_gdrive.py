import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
from sync_brain.soul_manager import get_gdrive_service, SOUL_FILES, BASE_DIR

def clean_drive():
    env_path = os.path.join(BASE_DIR, "backend-cortex", ".env")
    load_dotenv(env_path)
    folder_id = os.getenv("GDRIVE_FOLDER_ID")
    if not folder_id:
        print("[ERROR] No GDRIVE_FOLDER_ID found in .env")
        return

    service = get_gdrive_service()
    if not service:
        print("[ERROR] Failed to auth")
        return

    expected_files = list(SOUL_FILES.keys())
    print(f"Expected Core Files: {expected_files}")

    query = f"'{folder_id}' in parents and trashed = false"
    deleted_count = 0
    kept_count = 0
    kept_names = set()
    
    results = service.files().list(q=query, fields="nextPageToken, files(id, name, createdTime)", pageSize=1000).execute()
    files = results.get('files', [])
    
    print(f"Found {len(files)} total files in Google Drive folder.")
    files.sort(key=lambda x: x.get('createdTime', ''), reverse=True)
    
    for f in files:
        name = f['name']
        file_id = f['id']
        print(f"[DELETE] Wiping file: {name} ({file_id})")
        service.files().delete(fileId=file_id).execute()
        deleted_count += 1

    print(f"\n[OK] Google Drive Folder '{folder_id}' has been completely emptied. Deleted {deleted_count} files.")

if __name__ == "__main__":
    clean_drive()
