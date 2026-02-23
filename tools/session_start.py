#!/usr/bin/env python3
"""
tools/session_start.py — 開發 AI 開工簽到
執行: python tools/session_start.py
"""
import json
import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_DIR = os.path.join(BASE_DIR, "sync_brain")

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Cannot load {path}: {e}")
        return None

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def main():
    print_section("LifeOS Dev AI Session Start")
    print(f"  Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. Drift Check — version
    print_section("1. Drift Check")
    ctx_path = os.path.join(SYNC_DIR, "SYSTEM_CONTEXT.md")
    if os.path.exists(ctx_path):
        with open(ctx_path, "r", encoding="utf-8") as f:
            first_lines = [f.readline() for _ in range(5)]
        version_line = next((l for l in first_lines if "v3." in l), None)
        if version_line:
            print(f"  [OK] {version_line.strip()}")
        else:
            print("  [WARN] Version not found in SYSTEM_CONTEXT.md")
    else:
        print(f"  [ERROR] SYSTEM_CONTEXT.md not found at {ctx_path}")

    # 2. Evolution Log — last 5 events
    print_section("2. Recent Evolution (last 5 events)")
    evo_path = os.path.join(SYNC_DIR, "evolution_log.json")
    evo = load_json(evo_path)
    if evo and isinstance(evo, list):
        for entry in evo[-5:]:
            ts = entry.get("timestamp", "?")[:10]
            event = entry.get("event", "?")
            etype = entry.get("type", "")
            print(f"  [{ts}] [{etype}] {event}")
    else:
        print("  [WARN] Could not load evolution_log.json")

    # 3. Task Status
    print_section("3. Current Tasks")
    task_path = os.path.join(SYNC_DIR, "task.md")
    if os.path.exists(task_path):
        with open(task_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Show incomplete tasks
        incomplete = [l.strip() for l in lines if l.strip().startswith("- [ ]")]
        complete_count = sum(1 for l in lines if l.strip().startswith("- [x]"))
        if incomplete:
            print(f"  Completed: {complete_count} | Pending: {len(incomplete)}")
            print()
            for t in incomplete[:10]:
                print(f"  {t}")
        else:
            print(f"  [OK] All tasks complete! ({complete_count} done)")
    else:
        print("  [WARN] task.md not found")

    # 4. Quick reminder
    print_section("4. Dev AI Rules")
    print("  - You are DEV AI: work in tools/ and sync_brain/")
    print("  - System AI: backend-cortex/app/ (do not confuse)")
    print("  - SDK: google.genai (NOT google.generativeai)")
    print("  - Vectors: VECTOR(3072) only")
    print()
    print("  Ready to develop!")
    print()

if __name__ == "__main__":
    main()
