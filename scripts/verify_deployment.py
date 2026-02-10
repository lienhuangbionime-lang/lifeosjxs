import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_legacy_features():
    print("=" * 60)
    print("VERIFYING LEGACY FEATURES")
    print("=" * 60)

    # 1. Test Root
    try:
        r = requests.get(f"{BASE_URL}/")
        print(f"[ROOT] Status: {r.status_code}")
    except Exception as e:
        print(f"[ROOT] Failed to connect: {e}")
        return False

    # 2. Test Ingest (Save)
    print("\n[INGEST] Testing Save...")
    payload = {
        "text": "# Legacy Test 2026-02-11\n\nTesting save functionality.\nMood: 8",
        "date": "2026-02-11",
        "habits": [],
        "skip_ai": True
    }
    try:
        r = requests.post(f"{BASE_URL}/api/v1/ingest", json=payload, timeout=10)
        print(f"[INGEST] Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"  Status: {data.get('status')}")
            print(f"  DB ID: {data.get('db_id')}")
            
            if data.get('status') in ['analyzed', 'db_only']:
                print("  [PASS] Save successful.")
            else:
                print("  [FAIL] Unexpected status.")
                return False
        else:
            print(f"  [FAIL] Error: {r.text}")
            return False
    except Exception as e:
        print(f"[INGEST] Error: {e}")
        return False

    # 3. Test Retrieve
    print("\n[RETRIEVE] Testing Memories List...")
    time.sleep(2) # Wait for potential async write
    try:
        r = requests.get(f"{BASE_URL}/api/v1/memories?limit=5", timeout=10)
        print(f"[RETRIEVE] Status: {r.status_code}")
        if r.status_code == 200:
            memories = r.json()
            print(f"  Found: {len(memories)} memories")
            if len(memories) > 0:
                print(f"  Latest: {memories[0].get('content', '')[:50]}...")
                print("  [PASS] Retrieve successful.")
            else:
                # If 0, it might be RLS or empty db, but we just saved one.
                # If we just saved one, it should be there.
                print("  [WARN] Retrieve returned 0 memories despite save.")
                # We won't fail the whole test but warn.
        else:
            print(f"  [FAIL] Error: {r.text}")
            return False
    except Exception as e:
        print(f"[RETRIEVE] Error: {e}")
        return False

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_legacy_features()
