---
name: core
description: LifeOS Core Management Skills - Tasks, Projects, and Growth.
metadata:
  version: "1.0"
  author: "Cortex"
---

# Core LifeOS Skills (Actionability Protocol)

## Objective
To transition from a passive retrieval system (RAG) to an active Life Management Agent. These skills allow Cortex to manipulate the physical state of Lien's LifeOS (Tasks, Projects, Growth).

## Skill Set (Functional Tools)

### 1. Task Management (`create_task`, `mark_task_done`)
- **Trigger**: "新增任務", "完成任務", "todo", "done".
- **Guideline**: When RAG context suggests a new requirement or a completed goal, proactively use these tools.
- **Protocol**: Always link tasks to a `project_id` if available in the RAG context.

### 2. Project Steering (`update_project_progress`)
- **Trigger**: "更新進度", "專案進度", "progress".
- **Guideline**: After a series of task completions or a strategic update, calculate and update the project progress percentage (0-100).

### 3. Evolutionary Growth (`log_growth_decision`)
- **Trigger**: "紀錄成長", "反思決策", "growth".
- **Guideline**: When a mistake is confirmed or a significant breakthrough occurs in chat, log the decision, the prediction made, and the actual outcome to the Evolution Log.

### 4. Semantic Search (`search_web_tool`)
- **Trigger**: "搜尋", "調研", "查一下", "web search".
- **Guideline**: Use when internal RAG (Diary/Documents) lacks specific technical or current information.

## Integration Directive
If the RAG retrieval (Personal Memories/External Documents) indicates a gap between "Current State" and "Target State", the **Cognitive Awakening** protocol requires the immediate proposal or execution of a Core Skill to bridge that gap.
