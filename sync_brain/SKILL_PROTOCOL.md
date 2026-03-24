# SKILL_PROTOCOL.md: 技能邏輯框架 (Skill Hub)
**版本**: 1.0 (Aligning with Sovereign AI)

> 技能不是「功能」，它是執行手 (Claw) 根據大腦 (OpenClaw) 戰略所做出的「有目的的自動化」。

## 🧬 技能分類 (Skill Categories)

### 1. 演化類 (Evolution) ── 目標：對齊靈魂
*   **代表技能**: `report_synthesizer.py`
*   **邏輯**: 定期巡邏日誌中的非邏輯訊號，將其轉化為戰略報告。

### 2. 獲取與偵察類 (Acquisition & Recon) ── 目標：情報優勢
*   **代表技能**: `scout_engine.py`
*   **邏輯**: 不再被動等待。根據 `GOAL_MAP` 中的維度，主動巡邏全球趨勢（爬蟲、搜索、社群感知）。
*   **警報觸發**: 當外部變化（如新技術發布、市場波動）與您的專案或生命維度產生交集時，主動發出「主權提醒」。

### 3. 生成類 (Synthesis) ── 目標：物質產出
*   **代表技能**: `image_generator.py` (未來), `code_refactor.py` (未來)
*   **邏輯**: 將靈魂草稿轉化為物理文件或代碼。

## ⚙️ 技能呼叫協議
1.  **觸發**: 由 OpenClaw 識別出特定的「標籤」或「需求」後發起呼叫。
2.  **執行**: Claw 啟動對應的 `.py` 腳本，所有運算過程在本地完成。
3.  **同步**: 執行結果必須第一時間寫入 `sync_brain/` 供大腦與指揮官查閱。

### 4. 整合與邏輯類 (Integration & Logic) ── 目標：記憶迭代
*   **代表技能**: `memory_merger.py`, `skill_controller.py`
*   **邏輯**: 處理「舊資料」與「新資料」的衝突，確保系統的大腦不會出現認知混亂。
*   **功能**: 自動整合歷史存檔，將零散的日記提煉為核心定義。
