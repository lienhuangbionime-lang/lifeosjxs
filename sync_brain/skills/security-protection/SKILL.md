---
name: security-protection
description: "Use when git committing, handling API keys, or preventing secret leaks. Mandatory protection skill to prevent data exposure on GitHub."
---

# Skill: Security Protection (Zero-Leak)

## Overview
Implements the v4.6 Zero-Leak Policy. It acts as a semantic sentinel guarding the Commander's secrets.

## 🕒 使用時機 (Usage Timing)
- **GIT COMMIT/PUSH**: Check staged files for credentials.
- **API KEY CONFIG**: When setting up new services.
- **LOG EXPORT**: When sharing debug info with the user.

## 🛠️ Workflow

### 1. Secret Scanning
- Scan for `sk-...`, `ghp_...`, `AIza...`, and DB URLs.
- Redact them before any display or commit.

### 2. Environment Shielding
- Ensure `.env` files are in `.gitignore`.
- PROHIBIT hardcoding keys in Python files.

### 3. Redaction
Replace sensitive strings with `[REDACTED]`.

## 🛑 Failure Conditions
- Committing a raw secret triggers a mandatory Level 1 Post-Mortem.
