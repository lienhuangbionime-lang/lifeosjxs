# LifeOS v3.2 - AI Change Log
**記錄重要變更與架構決策，供未來 AI 參考**

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
