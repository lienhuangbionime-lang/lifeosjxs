---
name: handoff
description: 用於開發工作交接、進度紀實與 AI 協作接力。
metadata:
  version: "1.0"
  author: "Cortex"
---

# Developer Handoff Protocol

## Objective
Ensuring the next AI developer session (or current session end) has a surgical understanding of the system state, avoiding "Memory Drift" and redundant work.

## Output Format
1. **Current State (Component-level)**: 
   - 具體描述目前正在變動的 Module (如 `chat.py`, `skills.py`)。
   - 記錄已通過驗證的邏輯點。
2. **Technical Debt & Blockers**:
   - 尚未解決的 Lint 錯誤或邏輯缺陷 (Missing Edge Cases)。
   - 被暫時跳過的優化點。
3. **Crucial Context Keys**:
   - 導航至關鍵檔案的路徑與行數。
   - 重要的環境變數或資料庫表結構變動。
4. **Next Step Pipeline**:
   - 下一階段立即執行的第 1, 2, 3 步。

## Rules
- **No Fluff**: 直接給出路徑與技術細節。
- **Lint Aware**: 若有未修復的 Lint，必須記錄 ID 與原因。
- **Consistency**: 必須同步更新 `task.md` 與 `evolution_log.json`。
