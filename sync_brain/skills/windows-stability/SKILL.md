---
name: windows-stability
description: "Use when developing or running the LifeOS on Windows environments. Addresses critical encoding (CP950) and network (IPv6/Proxy) stability issues."
---

# Skill: Windows Stability Constraints

## Overview
Standardizes the fixes for Windows-specific architectural bottlenecks identified in v3.9 and v4.0.

## 🕒 使用時機 (Usage Timing)
- **BACKEND LOGGING**: Use for `print()` and `logger` formatting.
- **FRONTEND FETCH**: When configuring API base URLs on Windows.
- **CMD/POWERSHELL**: When running scripts that output text.

## 🛠️ Workflow

### 1. No Emojis in Prints
- **Strictly Forbidden**: Emojis in Python `print()` statements.
- **Instead Use**: `[OK]`, `[WARN]`, `[ERROR]`.

### 2. IPv6 Proxy Bypass
- **Strictly Forbidden**: Using `localhost:3000` in fetch or rewrites (causes 2s hang).
- **Instead Use**: `127.0.0.1:3000`.

### 3. Encoding Safety
- Ensure all file reads/writes specify `encoding='utf-8'` to avoid CP950 crashes.

## 🛑 Verification
- Verify that `npm run dev` doesn't hang on proxy calls.
- Run `python tools/smoke_test.py` to check logging stability.
