# 🧠 Cortex 核心能力現狀報告 (v3.5)

**更新日期**: 2026-02-11
**狀態**: 🚀 升級完成 (Post-Upgrade)

## 📊 系統能力升級清單

### 1. 檔案處理 (File Handling)
- **支援數量**: 單次單檔案 (Frontend Limit)
- **支援格式**: ✅ **PDF, TXT, MD**
- **圖片支援**: ✅ **已啟用** (支援 JPG, PNG, WEBP)
  - **說明**: 您的 Cortex 現在有「眼睛」了！上傳圖片，它會自動分析圖片內容並存入記憶。

### 2. 網址與 YouTube (URLs)
- **網址處理**: ✅ **已啟用** (自動爬取內容)
  - **說明**: 貼上 `https://...` 網址，Cortex 現在會自動去讀取網頁內容並總結。
- **YouTube**: ✅ **已啟用** (自動讀取字幕)
  - **說明**: 貼上 YouTube 連結，Cortex 會自動抓取影片字幕。

### 3. 語音支援 (Voice)
- **Capture 介面**: ✅ **支援** (即時語音轉文字)
- **Chat 介面**: ⚠️ **僅文字** (暫不支援直接語音輸入，請使用 Capture)

### 4. 使用額度 (Quota)
- **顯示狀態**: ✅ **真實計數**
- **功能**: 後端現在會記錄每次請求，並累計在資料庫中。
- **查看方式**: 系統狀態 API `/api/v1/system/status` 現在返回真實數據 (例如 `1495 / 1500`)。

### 5. 事實鏡像評分 (Fact-Based Scoring / Reality Check) [NEW]
- **功能狀態**: ✅ **已啟用 (核心技能)**
- **說明**: 這是由指揮官親自授予的技能。系統不再盲目接受使用者的主動評分，而是會主動提取行為「事實」，透過 `scoring_engine.py` 進行客觀計算。
- **作用**: 當使用者的自覺分數與行為事實不符時，Cortex 會主動提出證據進行糾正與引導。

---

## 🛠️ 下一步行動 (Required Actions)

為了啟用新功能，請執行以下步驟：

1. **重啟後端** (Restart Backend)
   ```bash
   # 在 backend-cortex 目錄
   Ctrl+C (停止)
   python main.py (啟動)
   ```

2. **執行資料庫遷移** (Database Migration)
   - 前往 Supabase Dashboard -> SQL Editor
   - 執行 `backend-cortex/infra/migrations/002_add_system_usage.sql` 的內容

3. **重新整理前端**
   - 刷新瀏覽器以加載新的 CortexChat 組件 (支援圖片選擇)。

---

## 🧪 測試報告 (Test Logs)
- **Vision Test**: `rag_service.py` logic updated with Gemini Vision.
- **Web Test**: `BeautifulSoup` scraper implemented.
- **Quota Test**: `system_usage` table schema prepared.
