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

### 1. Verification Probe
When encountering API failures (404/429), run the discovery tool:
```bash
python C:\Users\lien.huang\AppData\lifeosjxs\test.py
```

### 2. Registry Update
- Read `sync_brain/model_registry.json`.
- Update the system's internal model selection logic (`get_model()`) to use only 'verified_models'.

### 3. Cascading Fallback
1. Try the first `verified_model` in the tier (Fast/Smart).
2. If fails, rotate to the next ID in the verified list.

### 2. Discovery Loop
1. Verify connectivity to GenAI API.
2. Cross-reference available models with `sync_brain/registry.json`.
3. Report health via `model_report.py`.

## 🛑 Rules
- Use the `google.genai` (v1) SDK only.
