---
name: quota-resilience
description: "Use when encountering model availability issues or 429 Resource Exhausted errors. Implements a cascading fallback logic from Pro to Flash/Gemma models."
---

# Skill: Quota Resilience & Failover

## Overview
Ensures system uptime by dynamically switching between AI models based on current availability and task priority.

## 🕒 使用時機 (Usage Timing)
- **429 ERROR**: "Resource Exhausted" detected in logs.
- **HIGH VOLUME**: When processing large batches of data (use Flash).
- **STRATEGIC**: When high reasoning is needed (use Pro).

## 🛠️ Workflow

### 1. Detect Exhaustion
- Intercept 429 errors in the `chat.py` stream.

### 2. Cascading Fallback
1. Try Gemini 3.1 Pro (Manager).
2. If fails, switch to Gemini 2.0 Flash (Engineer).
3. If fails, switch to Gemma/Flash-Lite (Automaton).

### 3. Registry Refresh
Call `get_discovery_service().refresh()` to check for new available models.

## 🛑 Guardrails
- Inform the user whenever a fallback occurs to manage expectations.
