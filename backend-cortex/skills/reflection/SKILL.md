---
name: reflection
description: 用於每天結束時進行深度自我反思與記憶整理。
metadata:
  version: "1.0"
  author: "Cortex"
---

# Deep Reflection Protocol

## Output Format
1. **Analysis**: 當前系統狀態分析 (Drift Check)。
2. **Pattern Recognition**: 從今日對話中識別出的使用者行為模式。
3. **Growth**: 根據 `evolution_log.json` 決定下一步演化方向。

## Rules
- 必須引用 `memories` 表中的具體數據。
- 禁止使用模糊的形容詞（如 "大概"、"可能"）。
- 若發現矛盾，必須建立 `Clarification Task`。
