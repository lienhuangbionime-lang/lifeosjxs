---
name: collaboration-protocol
description: "Use when multiple AI agents (Claude, Pro, Flash) are collaborating on the same project. Defines clear role boundaries and communication channels."
---

# Skill: Multi-Agent Collaboration Protocol

## Overview
Standardizes communication and role boundaries to prevent "Too many cooks" architectural drift.

## 🕒 使用時機 (Usage Timing)
- **SESSION START**: When inheriting a task from another AI.
- **MAJOR ARCH CHANGE**: Must be proposed by Claude.
- **TASK UPDATE**: Must be done by Gemini Pro.

## 🛠️ Workflow

### 1. Identify Your Role
- **Claude (Architect)**: Design only. No code. Read `claude_brain/`.
- **Gemini Pro (Manager)**: Update `task.md` and `HANDOFF.md`.
- **Gemini Flash (Engineer)**: Write code. Run smoke tests.

### 2. Use the Hub
- **`task.md`**: Mission state.
- **`QUESTIONS.md`**: Messaging between AIs using tags like `[FLASH→PRO]`.
- **`evolution_log.json`**: Permanent history.

## 🛑 Guardrails
- **DO NOT** perform actions outside your role's mandate.
