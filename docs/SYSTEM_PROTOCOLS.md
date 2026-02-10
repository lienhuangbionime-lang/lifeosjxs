# LifeOS System Protocols & Architecture Memory
> **Last Updated:** 2026-02-11
> **Purpose:** 此文件記錄 LifeOS 關鍵架構決策與資料流協議。AI 在進行修改前必須閱讀此文件以確保連動性。

---

## 1. 核心資料流 (Ingest Pipeline)

### Architecture
- **Dual Flow**: 
  1. **Frontend (CaptureView)**: 負責接收輸入、顯示預覽。
  2. **Backend (Ingest API)**: 負責 AI 分析與邏輯處理。
  3. **Storage**: 同步寫入 **Supabase** (Cloud) 與 **Kernel** (Local C Binary)。

### Protocol: "Prompt as Code" (v7.1 Evolution)
- **Logic**: 日記的分析邏輯由 `backend-cortex/prompts/system_daily.md` 控制。
- **Parsing Strategy (Robust)**:
  - **Prompt Instruction**: 讓 AI 先輸出原生 Markdown，並在最後附帶 ````json ... ```` 區塊。
  - **Stripping Logic**: `sorter.py` 會提取最後一個 JSON 塊並將其從 `content` 中徹底移除，確保 UI 接收清爽的文本。
  - **JSON Content**: 包含 `mood`, `focus`, `energy`, `tags`, `category` 以及 `custom_metrics`。

### Model Decoupling (Stability Fix)
- 為避免 Python 命名空間衝突，API 層級的模型統一命名為 `IngestLogEntry` (定義於 `ingest_dual.py`)，系統/運算層級的模型則保留為 `LogEntry` (定義於 `app.models.gemini`)。
- **Data Flow**: `IngestRequest` -> `SorterAgent` (returns `LogEntry`) -> Transform to `IngestLogEntry` (for DB write).
| Field | Type | Source | Note |
|Str|Str|Str|Str|
| `content` | Markdown String | Sorter (Stripped) | 必須保留換行 (`whitespace-pre-wrap`) |
| `mood` | Int (1-10) | JSON Block | |
| `tags` | List[str] | JSON Block | 包含普通標籤與 `metric:key:val` |
| `category`| String | JSON Block | Life / Project |

---

## 2. 前端關鍵機制 (Frontend Mechanisms)

### Deployment & API
- **URL Strategy**:
  - Dev: `localhost:8000` (or enforced via `NEXT_PUBLIC_PYTHON_API_URL`)
  - Prod: `https://lifeosjxs.onrender.com`
  - Config: `next.config.js` (Rewrite Rules)
  
### Draft Protection
- **Mechanism**: `CaptureView` 使用 `localStorage` ('lifeos_capture_draft') 自動保存草稿。
- **Clear Trigger**: 僅在 **Save Success** 或 **Manual Clear** 時清除草稿。

### Brain Integration
- **Save to Brain**: 分析視窗中的按鈕。將 **AI 分析後的結果** (Markdown) 作為 `content` 存入，並設 `skipAi=true`。

---

## 3. 已知限制與規則 (Context Rules)

1. **Kernel Fallback**: 若無本地 C Kernel，系統自動降級為 Cloud-Only (Supabase)，不會報錯。
2. **Metadata Extension**: 若需新增指標 (e.g., Sleep)，請在 Prompt 中加入，Parser 會自動將其轉為 `metric:sleep:8` 格式的 Tag，無需修改 DB Schema。
3. **Graph Generation**: 目前依賴 `ingest_dual.py` 觸發 Embeddings，後續由 `Brain API` 產生圖譜節點。

---
**AI 指令：每次修改涉及資料流 (Ingest/Sorter/Frontend) 時，請務必檢查此文件以確保連動性不被破壞。**
