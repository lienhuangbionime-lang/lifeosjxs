---
name: graceful-handover
description: "Use when the system is about to be shut down or when an AI agent session is ending. Ensures all context is crystallized within the mandatory 15-minute window."
---

# Skill: Graceful Handover & Shutdown

## Overview
Ensures continuity across AI agent sessions. It triggers a high-density "final state extraction" before the system enters dormancy.

## 🕒 使用時機 (Usage Timing)
- **SHUTDOWN SIGNAL**: When receiving `SIGINT` or `SIGTERM`.
- **SESSION END**: When the current `task_boundary` is being finalized.
- **COMMANDER REQUEST**: When the user says "prepare for sleep" or "close session".

## 🛠️ Workflow

### 1. Final Crystallization (The 15-Min Window)
1. Scan `growth_logs` and `memories` for the last 12 hours.
2. Use Gemma to extract finalized decisions and architectural shifts.
3. Identify the "Next Step" for the next agent.

### 2. Sync-Brain Update
1. Update `sync_brain/evolution_log.json` with the session's major events.
2. Update `sync_brain/cortex_state.md` with the "Next Step (Handover)" field.

### 3. Persistence
Ensure all changes are written using `safe_write()` to avoid database corruption during shutdown.

## 🛑 Verification
- Check if `cortex_state.md` contains the newest summary.
- Verify `evolution_log.json` has the `micro_sync_shutdown` entry.
