---
name: schema-drift-defense
description: "Use when performing any database write operation (Insert, Update, Upsert). Essential for preventing system crashes due to missing columns or schema changes in the remote database."
---

# Skill: Schema Drift Defense (safe_write)

## Overview
Based on the lessons from the "PGRST204 Incident", this skill enforces the use of a resilient insertion wrapper.

## 🕒 使用時機 (Usage Timing)
- **DATABASE WRITES**: Every time data is sent to Supabase.
- **BACKGROUND TASKS**: When the AI generates content autonomously.
- **POST-MIGRATION**: When new fields are added but not yet synced locally.

## 🛠️ Workflow

### 1. Mandatory Core Wrapper
- **NEVER** use `db.table().insert()` directly.
- **ALWAYS** import `safe_write` from `app.core.database`.

### 2. Implementation Pattern
```python
from app.core.database import safe_write
safe_write(db.table("memories"), data, operation_type="insert")
```

### 3. Logic
- Strips invalid keys from payloads before retrying.
- Prevents silent crashes in background processes.

## 🛑 Rules
- Use only in the Backend Cortex.
