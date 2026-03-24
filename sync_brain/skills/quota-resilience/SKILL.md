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

### 1. Detect Exhaustion / Latency
- Intercept 429 (Resource Exhausted) or 503 (High Demand) errors.
- Monitor response latency (>10s triggers potential failover).

### 2. [v7.1] Cascading Fallback (2026 Stable Standard)
1. **Tier 1 (Flagship)**: Gemini 2.5 Flash (Production Worker).
2. **Tier 2 (Insight)**: Gemini 2.5 Pro (Conceptual Thinker).
3. **Tier 3 (Alternative)**: Gemini 3.0 Flash (Stable Redundancy).
4. **Tier 4 (Edge)**: Gemini 3.1 Flash-Lite-Preview (High Demand - Last Resort).

### 3. Registry Re-Ranking
Dynamically refresh `model_registry.json` via heuristic scoring that penalizes "lite-preview" tiers during high-demand spikes.

## 🛑 Guardrails
- **Fast Failover**: Max 3 retries with shallow backoff (1s, 3s) for UI-responsive sessions.
- **Fail-Safe Summary**: If all tiers are 503, return a structural summary from the DB to avoid blank insights.
