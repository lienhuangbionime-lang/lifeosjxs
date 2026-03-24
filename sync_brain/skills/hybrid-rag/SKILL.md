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
Search `memories` and `documents` tables using `text-embedding-004`.

### 2. Recency Weighting
Heuristically boost records from the last 7 days to ensure the AI remains present in the current life phase.

### 3. Isolation
- Documents = "Ground Truth / Technical".
- Memories = "Contextual / Personal".

## 🛑 Guardrails
- If results show `[NO RELEVANT MEMORIES]`, Admit ignorance.
