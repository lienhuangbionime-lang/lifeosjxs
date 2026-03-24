---
name: hybrid-rag
description: "Use when retrieving user memories or document knowledge. Combines semantic vector search with temporal recency weighting."
---

# Skill: Hybrid RAG & Recency Search

## Overview
Implements "Unified Awareness" by searching across temporal memories (Diary) and static knowledge (Documents) simultaneously.

## 🕒 使用時機 (Usage Timing)
- **CHAT REQ**: Every user message in standard chat mode.
- **REFLECTION**: When the system needs context to generate insights.
- **SEARCH TOOL**: When explicitly using the search function.

## 🛠️ Workflow

### 1. Vector Search
Search `memories` and `documents` tables using `gemini-embedding-2-preview`.

### 2. [v7.1] Neural Gap Resilience (Fallback)
If Vector Search returns zero results (Neural Gap):
- **Stage A: Content Match**: Perform exact `ilike` matching on `content` and `ai_insights`.
- **Stage B: Tag Overlap**: Search for overlapping tags in the memory array.
- **Stage C: Structural Injection**: Fetch `projects` metadata naming/description as a baseline.

### 3. Recency Weighting
Heuristically boost records from the last 7 days.

## 🛑 Guardrails
- If results show `[NO RELEVANT MEMORIES]`, trigger **Discovery Insight** (Prompt the user for local context).
