#!/usr/bin/env python3
"""
tools/arch_check.py — LifeOS 架構守護 Linter
執行: python tools/arch_check.py
在開發前跑一次，確保沒有架構違規。
"""
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- Rules Definition ------------------------------------------------

RULES = [
    {
        "id": "RULE-01",
        "name": "Deprecated SDK",
        "pattern": r"import\s+google\.generativeai",
        "message": "Use `from google import genai` / `google.genai` instead of `google.generativeai` (deprecated)",
        "severity": "ERROR",
        "include_dirs": ["backend-cortex/app", "tools", "sync_brain"],
        "extensions": [".py"],
    },
    {
        "id": "RULE-02",
        "name": "Wrong Vector Dimension",
        "pattern": r"VECTOR\(\s*(?!3072\b)\d+\s*\)",
        "message": "Only VECTOR(3072) is allowed (text-embedding-004 dimensions)",
        "severity": "ERROR",
        "include_dirs": ["backend-cortex/infra"],
        "extensions": [".sql"],
    },
    {
        "id": "RULE-03",
        "name": "Hardcoded HNSW on High-Dim Vector",
        "pattern": r"USING\s+hnsw",
        "message": "pgvector HNSW limit is 2000 dims — incompatible with VECTOR(3072). Use exact search.",
        "severity": "ERROR",
        "include_dirs": ["backend-cortex/infra"],
        "extensions": [".sql"],
    },
    {
        "id": "RULE-04",
        "name": "Deprecated Table Reference",
        "pattern": r'["\']LogEntry["\']|table\("LogEntry"\)',
        "message": "Table `LogEntry` is deprecated. Use `memories` instead.",
        "severity": "ERROR",
        "include_dirs": ["backend-cortex/app"],
        "extensions": [".py"],
    },
    {
        "id": "RULE-05",
        "name": "Tools importing app modules directly",
        "pattern": r"from app\.",
        "message": "tools/ should not import app.* directly — use HTTP API calls instead.",
        "severity": "WARN",
        "include_dirs": ["tools"],
        "extensions": [".py"],
        "exclude_files": ["arch_check.py", "migration_runner.py"],
    },
    {
        "id": "RULE-06",
        "name": "FastAPI routes in sync_brain",
        "pattern": r"@router\.(get|post|put|delete|patch)",
        "message": "sync_brain/ should not contain FastAPI routes — those belong in backend-cortex/app/api/",
        "severity": "ERROR",
        "include_dirs": ["sync_brain"],
        "extensions": [".py"],
    },
    {
        "id": "RULE-07",
        "name": "Windows-incompatible print with emoji",
        "pattern": r'print\(f?["\'].*[\U0001F300-\U0001FFFF].*["\']\)',
        "message": "Avoid emoji in print() — Windows cp950 may fail. Use [OK], [WARN], [ERROR] instead.",
        "severity": "WARN",
        "include_dirs": ["backend-cortex/app", "tools"],
        "extensions": [".py"],
    },
]

# ---- Scanner ---------------------------------------------------------

def scan_file(filepath: str, rule: dict) -> list[dict]:
    violations = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for i, line in enumerate(lines, 1):
            if re.search(rule["pattern"], line):
                violations.append({
                    "file": filepath,
                    "line": i,
                    "content": line.rstrip(),
                    "rule": rule,
                })
    except Exception:
        pass
    return violations


def get_files(include_dirs: list[str], extensions: list[str], exclude_files: list[str] = None) -> list[str]:
    result = []
    exclude_files = exclude_files or []
    for rel_dir in include_dirs:
        abs_dir = os.path.join(BASE_DIR, rel_dir.replace("/", os.sep))
        if not os.path.exists(abs_dir):
            continue
        for root, _, files in os.walk(abs_dir):
            for fname in files:
                if fname in exclude_files:
                    continue
                if any(fname.endswith(ext) for ext in extensions):
                    result.append(os.path.join(root, fname))
    return result


def main():
    print("\n[arch_check] LifeOS Architecture Linter")
    print(f"  Base: {BASE_DIR}\n")

    all_violations = []
    for rule in RULES:
        files = get_files(
            rule["include_dirs"],
            rule["extensions"],
            rule.get("exclude_files", [])
        )
        for fpath in files:
            violations = scan_file(fpath, rule)
            all_violations.extend(violations)

    if not all_violations:
        print("[OK] No architecture violations found.\n")
        sys.exit(0)

    errors = [v for v in all_violations if v["rule"]["severity"] == "ERROR"]
    warns = [v for v in all_violations if v["rule"]["severity"] == "WARN"]

    for v in all_violations:
        rel_path = os.path.relpath(v["file"], BASE_DIR)
        sev = v["rule"]["severity"]
        rid = v["rule"]["id"]
        msg = v["rule"]["message"]
        # Safe print for Windows cp950 — strip non-ascii chars
        safe_content = v["content"].strip()[:80].encode("ascii", "replace").decode("ascii")
        safe_msg = msg.encode("ascii", "replace").decode("ascii")
        print(f"  [{sev}] {rel_path}:{v['line']} [{rid}]")
        print(f"         {safe_content}")
        print(f"         -> {safe_msg}")
        print()

    print(f"Summary: {len(errors)} error(s), {len(warns)} warning(s)")

    if errors:
        print("\n[FAIL] Fix errors before continuing.")
        sys.exit(1)
    else:
        print("\n[PASS] No errors (warnings are informational).")
        sys.exit(0)


if __name__ == "__main__":
    main()
