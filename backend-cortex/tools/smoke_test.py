"""
LifeOS Smoke Test v1.0 — 核心 API 健康檢查
用法: python tools/smoke_test.py
前提: 後端已在 127.0.0.1:8000 運行 (uvicorn main:app)
"""
import httpx
import os
import sys
from pathlib import Path

# Load .env from backend-cortex root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

BASE = "http://127.0.0.1:8000"
HEADERS = {
    "X-Gemini-Key":    os.getenv("GEMINI_API_KEY", ""),
    "X-Supabase-URL":  os.getenv("SUPABASE_URL", ""),
    "X-Supabase-Key":  os.getenv("SUPABASE_KEY", ""),
    "Content-Type":    "application/json",
}

# (method, path, body, expect_status, expect_field_in_json)
TESTS = [
    # Core health
    ("GET",  "/",                                None,                           200, None),

    # Memory / Diary
    ("GET",  "/api/v1/memories/recent",          None,                           200, None),

    # Projects
    ("GET",  "/api/v1/projects/",                None,                           200, None),

    # Tasks
    ("GET",  "/api/v1/tasks/",                   None,                           200, None),

    # Chat (RAG)
    ("POST", "/api/v1/chat",                     {"message": "hi", "session_id": "smoke_test"}, 200, None),

    # System / Model status
    ("GET",  "/api/v1/system/status",            None,                           200, None),
]

print("=" * 55)
print("LifeOS Smoke Test v1.0")
print("=" * 55)

passed = 0
failed = 0

for method, path, body, expect_code, expect_field in TESTS:
    try:
        r = httpx.request(
            method,
            BASE + path,
            json=body,
            headers=HEADERS,
            timeout=20
        )
        ok = r.status_code == expect_code
        if ok and expect_field:
            try:
                ok = expect_field in r.json()
            except Exception:
                ok = False

        if ok:
            passed += 1
            print(f"[OK]    {method:4} {path}")
        else:
            failed += 1
            print(f"[FAIL]  {method:4} {path}  -> HTTP {r.status_code}")
            # Show first 200 chars of error body
            try:
                print(f"        {r.text[:200]}")
            except Exception:
                pass

    except httpx.ConnectError:
        failed += 1
        print(f"[ERR]   {method:4} {path}  -> Cannot connect to {BASE}")
        print(f"        [INFO] Is the backend running? Try: uvicorn main:app --reload")
        break  # No point continuing if server is down
    except Exception as e:
        failed += 1
        print(f"[ERR]   {method:4} {path}  -> {e}")

print("-" * 55)
print(f"Result: {passed} passed / {failed} failed")
print("=" * 55)

if failed > 0:
    print("[WARN] Some tests failed. Check the logs above before committing.")
    sys.exit(1)
else:
    print("[OK] All critical paths healthy.")
    sys.exit(0)
