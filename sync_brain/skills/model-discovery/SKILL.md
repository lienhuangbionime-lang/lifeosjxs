---
name: model-discovery
description: "Use when initializing AI models or checking environment health. Ensures the system is using verified, compatible models through the Discovery Service."
---

# Skill: Autonomous Model Discovery

## Overview
Prevents "Experimental Model Exhaustion" and ensures the Backend Cortex remains stable by using a discovery loop.

## 🕒 使用時機 (Usage Timing)
- **SYSTEM START**: First thing in `chat.py`.
- **QUOTA ERROR**: When 429 occurs, trigger a refresh of the model registry.
- **CONFIG SYNC**: When updating the `registry.json`.

## 🛠️ Workflow

### 1. Deep Probe (Live Audit)
Trigger a live audit of all Gemini models available to the API Key:
```bash
python backend-cortex/scripts/model_probe.py
```

### 2. [v7.1] Sandbox Verification (Mandatory)
Before promoting any model to `verified_models`, run a heartbeat test:
```bash
python backend-cortex/scripts/test_2_5.py
```
*Verification criteria: Response must be 'READY' or meaningful text.*

### 3. Smart Re-Ranking
Apply the **2026 Heuristic Scoring**:
- **Flagship**: +150 for `2.5-flash`, +140 for `2.5-pro`.
- **Legacy**: +80 for `2.0-flash`.
- **Penalty**: -60 for `lite`, -40 for `preview`.

### 4. Health Reporting
Update the `active_model_report_2026.md` artifact to reflect the current ecosystem status for the Commander.

## 🛑 Rules
- Never use a model with a 503 error profile in the primary tier.
- Prioritize **Stable GA** over **Preview** versions for production insights.
