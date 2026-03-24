---
name: glass-box-growth
description: "Use when an AI agent makes a significant strategic or architectural decision. Essential for auditable growth and future self-calibration."
---

# Skill: Glass Box Growth (Decision Logging)

## Overview
The Glass Box Protocol ensures that AI reasoning is transparent, auditable, and capable of self-correction. Every major choice must be recorded as a "Calibrated Event".

## 🕒 使用時機 (Usage Timing)
- **ARCHITECTURE CHANGE**: When changing a file structure or coding standard.
- **STRATEGIC CHOICE**: When presenting the user with multiple options.
- **USER PIVOT**: When the user provides feedback that changes the project direction.

## 🛠️ Workflow

### 1. Analyze the Context
Identify:
- **The Trigger**: Why we are making this decision.
- **The Options**: What are the alternatives?
- **The AI Prediction**: Which option does the AI think is best and why?

### 2. Record the Event
Call `log_growth_decision` with:
- `decision_context`: The scenario.
- `options_provided`: The matrix.
- `user_choice`: What was finally selected.
- `lessons_learned`: What did we learn from this alignment?

### 3. Persistence
The record is stored in `cortex_growth_logs` and mirrored in `sync_brain/evolution_log.json`.

## 🛑 Guardrails
- **DO NOT** hide the reasoning behind a decision.
- **DO NOT** ignore prediction mismatches; they are the high-signal data for future growth.
