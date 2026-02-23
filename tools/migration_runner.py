#!/usr/bin/env python3
"""
tools/migration_runner.py — 一鍵執行 SQL Migration 到 Supabase
執行: python tools/migration_runner.py infra/006_growth_logs_embedding.sql
需要: .env 中有 SUPABASE_URL + SUPABASE_SERVICE_KEY (不是 anon key)
"""
import sys
import os
import argparse
import urllib.request
import urllib.parse
import json

# Load .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    # Manual .env parse fallback
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")


def run_sql(sql: str) -> dict:
    """Execute SQL via Supabase REST API /rest/v1/rpc or /pg endpoint."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "[ERROR] SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env\n"
            "  SUPABASE_SERVICE_KEY = Project Settings > API > service_role key"
        )

    # Supabase supports raw SQL via the /sql endpoint (available for service_role)
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    # Fallback: use the REST query endpoint
    # Actually Supabase exposes /rest/v1/ for table operations, but for raw DDL
    # we need to use the SQL editor API or PostgREST RPC. 
    # Simplest approach: POST to the pg REST endpoint via anon+service key
    url = f"{SUPABASE_URL}/sql"

    payload = json.dumps({"query": sql}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "apikey": SUPABASE_SERVICE_KEY,
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return {"success": True, "response": body}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"success": False, "status": e.code, "error": error_body}


def split_statements(sql: str) -> list[str]:
    """Split SQL file into individual statements."""
    # Simple split on semicolons (handles most DDL)
    parts = []
    current = []
    for line in sql.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            continue  # Skip comments
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt and stmt != ";":
                parts.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            parts.append(stmt)
    return parts


def main():
    parser = argparse.ArgumentParser(description="LifeOS Migration Runner")
    parser.add_argument("sql_file", help="Path to .sql migration file (relative to project root)")
    parser.add_argument("--dry-run", action="store_true", help="Show SQL without executing")
    args = parser.parse_args()

    # Resolve path
    if not os.path.isabs(args.sql_file):
        sql_path = os.path.join(BASE_DIR, args.sql_file)
    else:
        sql_path = args.sql_file

    if not os.path.exists(sql_path):
        print(f"[ERROR] File not found: {sql_path}")
        sys.exit(1)

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"\n[Migration] {os.path.basename(sql_path)}")
    print(f"  Supabase: {SUPABASE_URL or '[NOT SET]'}")

    if args.dry_run:
        print("\n[DRY RUN] SQL to execute:")
        print("-" * 50)
        print(sql_content)
        return

    # Execute full file as one statement (DDL is usually sequential)
    print("\n[Executing...]")
    result = run_sql(sql_content)

    if result.get("success"):
        print("[OK] Migration applied successfully.")
        print(f"     Response: {result.get('response', '')[:200]}")
    else:
        print(f"[ERROR] Migration failed (HTTP {result.get('status', '?')})")
        print(f"  {result.get('error', '')[:500]}")
        print()
        print("  Hint: Try running the SQL manually in Supabase SQL Editor:")
        print(f"  {SUPABASE_URL.replace('/rest/v1', '')}/project/*/sql")
        sys.exit(1)


if __name__ == "__main__":
    main()
