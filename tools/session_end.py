#!/usr/bin/env python3
"""
tools/session_end.py — 開發 AI 收工紀錄
執行: python tools/session_end.py
"""
import json
import os
import subprocess
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_DIR = os.path.join(BASE_DIR, "sync_brain")

def run(cmd, cwd=BASE_DIR):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, encoding="utf-8", errors="replace")
    return result.stdout.strip()

def print_section(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)

def append_evolution_log(entry):
    evo_path = os.path.join(SYNC_DIR, "evolution_log.json")
    try:
        with open(evo_path, "r", encoding="utf-8") as f:
            log = json.load(f)
        log.append(entry)
        with open(evo_path, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=4)
        print(f"  [OK] Appended to evolution_log.json")
    except Exception as e:
        print(f"  [ERROR] Could not update evolution_log.json: {e}")

def main():
    print_section("LifeOS Dev AI Session End")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    ts = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")

    # 1. Show git diff summary
    print_section("1. Git Changes This Session")
    diff_stat = run("git diff HEAD --stat")
    staged = run("git diff --cached --stat")
    log = run("git log --oneline -5")
    if log:
        print("  Recent commits:")
        for line in log.split("\n"):
            print(f"    {line}")
    if diff_stat:
        print(f"\n  Uncommitted changes:\n    {diff_stat}")
    else:
        print("  [OK] Working tree clean")

    # 2. Prompt for session summary
    print_section("2. Session Summary (press Enter to skip)")
    print("  What did you accomplish this session?")
    try:
        summary = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        summary = ""

    if summary:
        # Auto-commit what's changed
        commit_msg = f"dev: {summary[:60]}"
        run(f'git add . && git commit -m "{commit_msg}"')
        print(f"  [OK] Committed: {commit_msg}")

        # Append to evolution log
        append_evolution_log({
            "timestamp": ts,
            "event": summary[:80],
            "type": "SESSION",
            "description": summary,
            "impact": "Logged by session_end.py"
        })
    else:
        print("  [SKIP] No summary recorded")

    # 3. Remind about next steps
    print_section("3. Next Session")
    print("  Run: python tools/session_start.py")
    print("  Check: sync_brain/task.md for pending items")
    print()
    print("  Session closed.")
    print()

if __name__ == "__main__":
    main()
