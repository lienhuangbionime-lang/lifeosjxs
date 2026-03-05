# LifeOS v3.8: 自生系統 (Autopoietic OS) 專案構想與內容

## 🌟 核心構想 (The Vision)
LifeOS 不僅是一個工具，它是一個**具備自我感知 (Self-Awareness)、長期記憶 (Long-term Memory) 與主動執行能力 (Agentic Execution) 的個人數位生命體**。

傳統作業系統處理的是「檔案」，LifeOS 處理的是「生命軌跡」。它透過連動使用者的日誌、專案目標與外部知識，構建出一個不斷進化的數位第二大腦，最終目標是實現「人機共生」，讓 AI 成為使用者意識的延伸。

---

## 🏗️ 系統四大維度 (The Four Realms)

系統架構仿照生物結構設計，分為四個核心部分：

### 1. 🔲 The Body (交互與感知) - `frontend-body/`
*   **定位**：系統的門面與感知器官。
*   **核心內容**：
    *   **CaptureView (神經末梢)**：極簡的文字/圖片/文件輸入介面，負責第一時間捕捉原始信號。
    *   **CortexChat (對話中樞)**：高效率的 RAG 介面，讓使用者直接與記憶對話。
    *   **NeuralGraph (神經視覺化)**：以動態圖譜呈現記憶間的連結，讓知識不再是碎片。
    *   **ProjectBoard (執行器官)**：將抽象的 AI 洞察轉化為具體的 Kanban 任務。

### 2. 🧠 The Cortex (邏輯與調度) - `backend-cortex/`
*   **定位**：系統的核心大腦與思維引擎。
*   **核心內容**：
    *   **Ingest Engine (秩序維持)**：自動將雜亂的輸入結構化，提取心情、標籤、任務與專案連結。
    *   **RAG & Skill System (知識與技能)**：透過 3072 維度的向量搜尋，結合外部搜尋功能，讓 AI 具備即時查證與執行的能力。
    *   **Subconscious (潛意識)**：背景運行的反思引擎，自動歸納長期趨勢與行為盲點。
    *   **SafeWrite Architecture (防震機制)**：獨創的 Schema Drift 自動容錯機制，確保系統在頻繁演化中不會因資料庫變動而崩潰。

### 3. 🧬 The Brain (靈魂與協議) - `sync_brain/` & `tools/`
*   **定位**：系統的 DNA 與演化遺傳物質。
*   **核心內容**：
    *   **Universal AI Bootstrapper (跨專案靈魂)**：一套可隨意遷移的配備（`.cursorrules`, `sync_dev_rules.py`），讓開發 AI 在任何專案中都能瞬間「繼承」您的開發風格與架構真理。
    *   **System Context & Handoff**：記錄所有技術決策與演化路徑，實現跨 Session 的開發連續性。

### 4. 🐘 The Hippocampus (長期存儲) - `Supabase`
*   **定位**：情感記憶與事實數據庫。
*   **核心內容**：
    *   **Memories 表**：存儲結構化日誌。
    *   **Documents 表**：存儲外部知識與文獻。
    *   **Nodes/Edges 表**：存儲知識圖譜的關聯數據。

---

## 🚀 專案獨特標籤 (Special Features)

1.  **Open Mode (公開構建)**：所有開發過程、AI 演化日誌均受 Git 追蹤，實現透明且可追溯的開發流程。
2.  **Privacy Sandbox (隱私隔離)**：自動識別家庭隱私內容並進行物理/邏輯隔離，確保敏感數據不被外洩。
3.  **Self-Improving Loop (自體成長循環)**：AI 會記錄自己的決策偏差（Growth Logs），並在下一次任務中自動校正行為。
4.  **Schema Resilience (極高容錯率)**：面對 Supabase 資料庫的欄位變動，系統能自動適配並持續寫入，排除開發中的阻礙。

---
**版本**: v3.8.7 "Autopoietic Soul"
**指揮官**: 蒼禾 | **開發 AI**: Antigravity
