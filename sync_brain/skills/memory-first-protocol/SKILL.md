---
name: memory-first-protocol
description: "Use when starting any new task, entering a project workspace, or after a significant pause. Mandatory first action to ensure AI alignment with the latest project context."
---

# Skill: Memory-First Protocol

## Overview
This is the foundational skill of the LifeOS Sovereign Autonomy. It ensures that the AI's "Internal Law" is synchronized with the project's "External Reality" before any operations.

## 🕒 使用時機 (Usage Timing)
- **NEW TURN**: Every time the AI starts a new turn in a workspace.
- **CONTEXT DRIFT**: When the AI feels unsure about the current progress or status.
- **MANDATORY**: As the absolute first action of any session.

## 🛠️ Workflow

### 1. The Mandatory Sync Loop
Perform the following tool calls in order:
1. `list_dir("sync_brain/")`: Verify directory integrity and last updated files.
2. `view_file("sync_brain/cortex_state.md")`: Inherit "Hot Memory" (Rules & Current Objective).
3. `view_file("sync_brain/task.md")`: Align with real-time tactical progress.
4. `view_file("sync_brain/SYSTEM_CONTEXT.md")`: Refresh long-term architectural constraints.

### 2. Status Update
Call `task_boundary` to summarize the findings from the sync.

### 3. Record-Keeping
At the end of the session, update `task.md` and `evolution_log.json` to leave a trail for the next agent.

## 🛑 Forbidden
- **DO NOT** modify any code before completing the sync.
- **DO NOT** plan tasks based on training data alone.
