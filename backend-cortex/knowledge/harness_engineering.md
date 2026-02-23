# Harness Engineering — 開發 AI 知識文件

> **知識類型**: 架構範式 / 開發方法論  
> **來源**: LangChain Blog + OpenAI Codex 實戰報告  
> **日期**: 2026-02-24

---

## 🎯 核心概念

**Harness Engineering** = 不改模型，改「環境」。

> 「Harness 的目標是把模型固有的不穩定智慧，塑形成我們需要的任務表現。」 — LangChain

類比：馬具（harness）不是改變馬的能力，而是讓人能夠精準駕馭馬的力量。

---

## 📊 LangChain 實驗成果

指標只改 Harness，模型固定不換（`gpt-5.2-codex`）：

| Before | After | 提升 |
|---|---|---|
| 52.8 分 | 66.5 分 | **+13.7 點** |

Terminal Bench 2.0：89 個任務（ML / Debug / Biology）

---

## 🔧 Harness 的「旋鈕」（Knobs）

### 1. Context Engineering（上下文工程）
- 給 Agent 目錄結構、可用工具、最佳實踐
- 問題根源往往是「缺乏上下文」，不是模型能力不足
- **LifeOS 對應**: `system_cortex.md` + `SYSTEM_CONTEXT.md` + `evolution_log` 注入

### 2. Self-Verify（自我驗證）
- 模型天生偏向第一個可行方案
- 強制要求 Agent 用測試驗證自己的輸出
- **LifeOS 對應**: `scoring_engine.py` validation loop in `ingest.py`

### 3. Trace Analysis（追蹤分析）
- 每個 Agent action 存入追蹤系統（LangSmith）
- 用 trace 找出失敗模式：推理錯誤 / 沒遵守指令 / 超時
- **LifeOS 對應**: `cortex_growth_logs` 記錄決策 + 誤判率

### 4. Step Back（後退重思）
- 強制 Agent 在執行前停下來重新評估計劃
- 類似 Glass Box Decision Matrix（先預測再行動）

### 5. Compute Budget（算力預算）
- 根據任務複雜度動態調整推理深度
- **LifeOS 對應**: `gemini-flash-lite` vs `gemini-pro` 的自動切換

---

## 🏗️ OpenAI Codex 實戰：Harness Engineering 四個原則

### 1. 讓應用對 AI 可讀
- UI、logs、metrics 直接暴露給 AI
- AI 可查 LogQL / PromQL 進行自我診斷
- Git worktree 讓 AI 可以為每次修改啟動獨立沙盒
- **關鍵**: 瓶頸是人類 QA 能力，解法是讓 AI 能自己 QA

### 2. 架構強制與品味約束
- 明確的層次邊界（不規定實現，只規定邊界）
- Custom Linter 機械強制規則（Linter 本身也是 AI 生成的）
- **LifeOS 對應**: `registry.json` 定義 Schema 邊界，`registry.json` 本身就是 AI 的架構約束

### 3. 高吞吐量改變合併哲學
- PR 週期短暫，不穩定測試通過後續運行解決
- 「修正成本低，等待成本高」
- **對開發 AI 的啟示**: 快速 commit，保持 main 可運行，不要完美主義

### 4. 完全自主的臨界點
- 當測試、驗證、審查、反饋都被編碼進系統後，AI 可以端到端驅動新功能
- 人類只在需要判斷時才介入（升級機制）

---

## 🤖 Factory Droid — 最被低估的 AI Coding Agent

**Eno Reyes（Factory 共同創辦人）的核心觀點：**

### Skills vs MCPs vs Hooks
- **Skills**: 給 AI 的技能文件（700 字可讓 AI 像資深 PM 思考）
- **MCPs**: 整合外部工具的協議
- **Hooks**: 特定事件觸發的自動操作
- 選用時機不同：需要知識用 Skill，需要工具用 MCP，需要自動化用 Hook

### Spec Mode vs Plan Mode
- **Spec Mode**: 先定義需求規格（What），讓 AI 提問直到充分理解
- **Plan Mode**: 再規劃執行步驟（How）
- 順序很重要：Spec 先，Plan 後

### Real Engineers vs Vibe Coders
- Real engineers 把 AI 當「執行工具」，自己保持架構決策權
- Vibe coders 讓 AI 做所有決定 → 代碼債務快速累積
- **LifeOS 使命一致**: 蒼禾（指揮官）做決策，AI 執行

---

## 🎯 LifeOS Harness Engineering 對應表

| Harness 要素 | LifeOS 現況 | 建議強化 |
|---|---|---|
| **Context Engineering** | `system_cortex.md` + `evolution_log` 注入 ✅ | 加入 `registry.json` schema 片段 |
| **Self-Verify** | `scoring_engine` validation ✅ | 接 `daily_reflection` 驗證 |
| **Trace / Growth Logs** | `cortex_growth_logs` + 語意搜尋 ✅ | 完整 |
| **Architecture Constraints** | `registry.json` schema ✅ | 加入 Custom Linter |
| **Sandboxing** | 本地 `data/memories/` 隔離 ✅ | 評估 Docker worktree |
| **Upgrade to Human** | `drift_check()` HALT 機制 ✅ | 完整 |

---

**最後更新**: 2026-02-24  
**相關文件**: `sync_brain/SYSTEM_CONTEXT.md`, `tools/AI_MEMORY.md`
