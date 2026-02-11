## 📅 2026-02-11: Version 3.6.0 (Cortex Intelligence & UI Evolution)

### 1. Stateful & Context-Aware Chat (RAG Evolution)
*   **Memory Retrieval**: 實作了基於 Vector Search 的記憶檢索。`rag_service.py` 現在能從 Supabase `memories` 目錄查找相關歷史。
*   **System Context Injection**: AI 現在在回答前會自動獲取「當前活躍專案」與「近期日記摘要」，實現真正的 Context-Aware。
*   **Multi-turn Conversation**: `chat.py` 支援傳遞歷史對話紀錄，讓 Cortex 具備上下文連貫對談能力。
*   **Real-time Embedding**: 修正 `ingest_dual.py`，現在每一條日記存入時，都會同步調用 `gemini-embedding-001` 產生向量並存入資料庫。

### 2. UI Transformation (Neutral Assistant Look)
*   **Aesthetic Pivot**: 從復古的「ZELFA // TERMINAL」轉向現代簡潔的「Cortex Assistant」風格（Indigo / Slate 配色）。
*   **Mobile Optimization**: 將聊天視窗寬度縮小至 360px，並優化響應式佈局，解決手機版遮擋且無法移動的問題。
*   **Custom Markdown Styling**: 手寫 Markdown 渲染樣式，擺脫對 `@tailwindcss/typography` 的依賴，確保在不同環境下視覺的一致性。

### 3. Client-Side Model Governance
*   **System Core Modal**: 新增對話框內的設定面板，允許使用者手動切換模型（如 Gemini 1.5 Pro/Flash）與管理 API Key。
*   **Local Persistence**: 設定值存儲於 `localStorage`，兼顧隱私與使用的便利性。

---

## 📅 2026-02-11: Version 3.5.0 (Agentic Ingest Evolution)


### 1. "Prompts as Code" 實作
為了讓使用者能自由維護日記分析格式，將 System Prompt 從程式碼中抽離：
*   **外部化**: 建立 `backend-cortex/prompts/system_daily.md`。
*   **動態讀取**: `SorterAgent` 現在會於每次請求時動態讀取該 Markdown 檔案。
*   **維護性**: 使用者只需修改 Markdown 檔案即可調整 AI 思考邏輯與日記格式，無需進版或重啟。

### 2. 資料提取協議 (Hidden JSON Protocol)
為了解決 LLM 輸出 JSON 時換行符易錯的問題，並提高解析效率：
*   **混合模式**: 讓 AI 輸出「原生 Markdown」(用於顯示) + 「末尾 JSON 塊」(用於數據)。
*   **Python 解析器**: `SorterAgent._parse_markdown` 使用 Regex 提取末尾 JSON，並自動將其從給使用者看的 `content` 中剔除。
*   **擴充性**: 新增指標 (如 Sleep) 會自動轉為 `metric:sleep:X` 格式的標籤，實現未來數據無痛增加。

### 3. 前端強化與草稿保護 (UI/UX)
*   **Auto-Draft**: `CaptureView` 引入 `localStorage` 保存機制，切換頁面不再遺失輸入內容。
*   **Save to Brain**: 分析終端機中新增「💾 SAVE TO BRAIN」按鈕。
    *   **Logic**: 修正了過去只能存入「原始內容」的限制，現在可直接將「AI 整理後的 Markdown」存入資料庫。
*   **API 靈活性**: `next.config.js` 支援 `NEXT_PUBLIC_PYTHON_API_URL` 環境變數，方便本地前端連接遠端生產環境。

### 4. 穩定性修復 (Backend Fixes)
*   **路徑修復**: `ingest_dual.py` 的 `sys.path` 修正為指向 `backend-cortex` 根目錄，解決 `app` 模組導入問題。
*   **模型解耦**: 將 API 請求模型命名為 `IngestLogEntry`，與系統內部的 `LogEntry` 區分，解決同名衝突導致的 500 錯誤。

---

## 📅 2026-02-11: Version 3.4.0 (Kernel Evolution)

### 1. C Kernel 重大升級
核心儲存引擎 `life_v3.c` 經歷了三次迭代，進化為真正可用的「數位原版」：

*   **v3.2 (Temporal Drift Fix)**:
    *   引入 `get_global_day_offset` 取代簡單的年份乘法。
    *   修正閏年 (Leap Year) 導致的 Index 錯位問題。
    *   **Immutability Policy Change**: 從「禁止覆寫」改為「Append-Only」，允許修正過去的錯誤，但保留所有歷史軌跡。

*   **v3.3 (Genesis Header)**:
    *   引入 `LifeHeader` 結構，佔用檔案前 32 bytes。
    *   **Self-Describing Data**: 檔案現在會自我描述 `BASE_YEAR`，防止程式碼更新導致舊檔案讀取錯亂。

*   **v3.4 (Dynamic Genesis)**:
    *   **User-Centric Timeline**: 不再寫死 `2024` 為起始年。
    *   當使用者**第一次寫入**時，系統會自動將「當下年份」鎖定為該使用者的 `Genesis Year`。
    *   這確保了每位使用者的資料庫都是最小化且針對個人生命週期優化的。

### 2. Python Driver 適配 (Adapter Pattern)
為了配合 C Kernel 的演進，`kernel_driver.py` 進行了架構重構：

*   **從 `ctypes` 轉向 `subprocess`**:
    *   不再依賴脆弱的 DLL/Shared Object (`.so` / `.dll`)Loading。
    *   改為直接調用編譯好的 CLI 工具 (`life.exe`)。
    *   **優點**: 更穩定，且更容易測試 (CLI 可以單獨手動執行)。
*   **Cloud-Only Fallback**:
    *   新增檢測機制：如果 `life.exe` 不存在 (未編譯)，自動降級為「僅雲端模式」，不影響 App 運行。

---

## 📅 2026-02-10: Version 3.2.0 (Cleanup & Kernel Integration)

### 1. 目錄清理與重組 (Directory Cleanup)
為了減少專案體積並提高可維護性，執行了以下清理：
- **刪除** `backend-cortex/venv/` (約 300MB): 開發環境可隨時重建。
- **刪除** `.next/` (約 120MB): 前端構建產物可隨時重建。
- **刪除** `backend-cortex` 下的開發測試檔案 (`debug_*.py`, `check_*.py`, `test_*.py`): 約 10 個檔案，不影響生產環境。
- **移動** 文檔到 `docs/` 目錄: 建立 `docs/archive/` 用於存放歷史記錄。
- **移動** 腳本到 `scripts/` 目錄: 包含清理與編譯腳本。

### 2. C Kernel 整合 (C Kernel Integration)
為了實現「數位原版」(Digital Original) 概念，引入了 C 語言核心：
- **新增** `backend-cortex/kernel/life_v3.c`: Append-Only 的二進制儲存核心。
- **新增** `backend-cortex/kernel_driver.py`: Python 驅動程式。
- **新增** `backend-cortex/routers/ingest_dual.py`: 實現雙寫入策略 (Supabase + Kernel)。
- **決策**: 為了效能與不可變性，核心數據應同時寫入 Kernel。

### 3. 組件移除與修復 (Component Removal & Fixes)
- **移除** `frontend-body/components/Dashboard.tsx`: 舊版儀表板，已被 `CardStackDashboard.tsx` 取代。
- **移除** `frontend-body/components/SettingsModal.tsx`: 功能與 `SettingsView.tsx` 重複且未完成。
- **移除** `frontend-body/components/MarkdownRenderer.tsx`: 可用標準套件取代。
- **修復** `SettingsView.tsx`: 移除對已刪除 `SettingsModal` 的引用，並清理未使用的 `Shield` icon。

### 4. 保留功能 (Preserved Features)
雖未完全整合，但保留以下組件供未來「Brain / Graph」功能使用：
- `frontend-body/components/NeuralGraph.tsx`
- `frontend-body/components/GraphView.tsx`
- `frontend-body/components/ContextModal.tsx`

---

## 🔮 未來規劃 (Future Roadmap)

### Phase 2: 目錄結構重組 (Pending)
目前的目錄結構 (`frontend-body`, `backend-cortex`) 仍為舊版。
計劃遷移至標準的 `src/` 結構 (`src/frontend`, `src/backend`)。
**狀態**: 暫緩執行，以免影響當前開發流程。相關腳本保留在 `scripts/reorganize.ps1`。

### Brain 功能實作
下一步應將 `NeuralGraph` 與後端的 `Knowledge Graph` (待開發) 連接，實現視覺化的關聯分析。

---

**AI Note**: 在進行任何重大結構變更前，請先參考 `docs/SAFE_EXECUTION_PLAN.md`。
