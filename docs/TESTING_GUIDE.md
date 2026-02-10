# LifeOS v3.5 - 完整系統測試指南

## 🎯 測試目標

驗證以下系統組件的完整連動：
1. ✅ 後端 API (FastAPI)
2. ✅ 資料庫 (Supabase)
3. ✅ AI 分析 (Gemini)
4. ✅ 前端介面 (Next.js)
5. ✅ 所有分頁功能
6. ✅ 雲端同步

---

## 📋 測試前準備

### 1. 啟動後端
```bash
cd backend-cortex
python main.py
```

**預期輸出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
[OK] C Kernel verified (Binary found)
# 或
[WARN] C Kernel binary not found. Running in Cloud-Only mode.
```

### 2. 啟動前端
```bash
cd frontend-body
npm run dev
```

**預期輸出**:
```
ready - started server on 0.0.0.0:3000
```

### 3. 檢查環境變數

**後端 (.env)**:
```bash
GOOGLE_API_KEY=xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

**前端 (.env.local)**:
```bash
NEXT_PUBLIC_PYTHON_API_URL=http://127.0.0.1:8000
```

---

## 🧪 自動化測試

### 執行完整測試
```bash
python test_system_integration.py
```

### 測試項目

#### 1. Backend Health Check
- 測試後端是否運行
- 檢查 `/health` 端點

#### 2. Supabase Connection
- 測試資料庫連接
- 查詢 `memories` 表

#### 3. AI Analysis (Gemini)
- 測試 AI 分析功能
- 驗證 Gemini API 連接

#### 4. Save to Database
- 測試雙寫策略
- 驗證 Supabase + C Kernel

#### 5. Retrieve Memories
- 測試讀取功能
- 驗證資料完整性

#### 6. API Endpoints
- `/health` - 健康檢查
- `/api/v1/system/status` - 系統狀態
- `/api/v1/memories` - 記憶查詢
- `/api/v1/ingest` - 資料攝取

#### 7. Schema Registry
- 測試 Schema 演進工具
- 驗證 `schemas/registry.json`

---

## 🖥️ 手動測試（前端分頁）

### Tab 1: Capture (捕捉)

**測試步驟**:
1. 打開 http://localhost:3000
2. 在輸入框輸入日記
3. 點擊 **"INGEST & ANALYZE"**
4. 等待 AI 分析（5-10 秒）
5. 檢查 Terminal 顯示分析結果
6. 點擊 **"SAVE TO BRAIN"**
7. 檢查 Toast 提示「已儲存」

**預期結果**:
- ✅ AI 分析成功
- ✅ Terminal 顯示 Markdown 格式內容
- ✅ 顯示心情、專注、能量指標
- ✅ 存檔成功

**常見問題**:
- ❌ 500 錯誤 → 檢查後端日誌，可能是 emoji 問題
- ❌ 分析失敗 → 檢查 GOOGLE_API_KEY
- ❌ 存檔失敗 → 檢查 Supabase 連接

---

### Tab 2: Brain (大腦圖譜)

**測試步驟**:
1. 切換到 **Brain** 分頁
2. 等待圖譜載入（2-3 秒）
3. 檢查是否顯示節點和連線
4. 嘗試拖拽節點
5. 嘗試縮放（滾輪）
6. 懸停節點查看詳情
7. 點擊節點查看完整內容

**預期結果**:
- ✅ 顯示力導向圖
- ✅ 節點顏色根據心情變化
  - 高心情 (≥8) = 霓虹綠
  - 低心情 (≤3) = 霓虹粉
  - 一般 = 霓虹青
- ✅ 標籤節點 = 霓虹紫
- ✅ 可以拖拽和縮放
- ✅ 懸停顯示 tooltip

**常見問題**:
- ❌ 空白畫面 → 檢查是否有日記資料
- ❌ 節點不顯示 → 檢查 console 錯誤
- ❌ 無法互動 → 檢查 D3.js 載入

---

### Tab 3: List (列表)

**測試步驟**:
1. 切換到 **List** 分頁
2. 檢查日記列表
3. 點擊某個條目
4. 查看詳細內容
5. 嘗試編輯（如果有功能）
6. 嘗試刪除（如果有功能）

**預期結果**:
- ✅ 顯示所有日記
- ✅ 按日期排序（最新在前）
- ✅ 顯示心情指標
- ✅ 可以點擊查看詳情

**常見問題**:
- ❌ 空列表 → 檢查資料庫是否有資料
- ❌ 無法點擊 → 檢查 onClick 事件

---

### Tab 4: Projects (專案)

**測試步驟**:
1. 切換到 **Projects** 分頁
2. 點擊 **"Create Project"**
3. 輸入專案名稱和描述
4. 儲存專案
5. 檢查專案列表
6. 點擊專案查看詳情

**預期結果**:
- ✅ 可以創建專案
- ✅ 專案顯示在列表中
- ✅ 可以查看專案詳情

**常見問題**:
- ❌ 創建失敗 → 檢查 API 端點
- ❌ 列表空白 → 檢查資料庫 `projects` 表

---

### Tab 5: Dashboard (儀表板)

**測試步驟**:
1. 切換到 **Dashboard** 分頁
2. 檢查統計卡片
3. 查看心情趨勢圖
4. 查看習慣追蹤

**預期結果**:
- ✅ 顯示統計數據
- ✅ 顯示圖表
- ✅ 數據正確

---

### Tab 6: Settings (設定)

**測試步驟**:
1. 切換到 **Settings** 分頁
2. 檢查系統狀態
3. 查看 AI 配額
4. 測試設定變更

**預期結果**:
- ✅ 顯示系統狀態
- ✅ 顯示 AI 剩餘配額
- ✅ 設定可以儲存

---

## ☁️ 雲端可行性測試

### Supabase 連接測試

**方法 1: 使用測試腳本**
```bash
python test_system_integration.py
```

**方法 2: 手動測試**
```bash
# 測試寫入
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"text":"測試","date":"2026-02-11","habits":[],"skip_ai":true}'

# 測試讀取
curl http://127.0.0.1:8000/api/v1/memories?limit=5
```

**預期結果**:
- ✅ 寫入成功，返回 `status: "synced"` 或 `"db_only"`
- ✅ 讀取成功，返回 JSON 陣列

### Supabase Dashboard 驗證

1. 登入 https://supabase.com/dashboard
2. 選擇您的專案
3. **Table Editor** → 選擇 `memories`
4. 檢查是否有新增的資料
5. 驗證欄位：
   - `id` (UUID)
   - `content` (TEXT)
   - `date` (DATE)
   - `mood`, `focus`, `energy` (INT)
   - `tags` (TEXT[])

**預期結果**:
- ✅ 表格存在
- ✅ 資料正確
- ✅ 時間戳正確

---

## 🐛 常見問題排查

### 問題 1: 後端 500 錯誤

**症狀**: 前端顯示「Submission failed: Cortex Error (500)」

**可能原因**:
1. Python print() 中有 emoji（Windows 編碼問題）
2. Supabase 連接失敗
3. 資料庫表不存在

**解決方案**:
```bash
# 1. 檢查後端日誌
# 查看 terminal 輸出

# 2. 確認所有 emoji 已移除
grep -r "print.*emoji" backend-cortex/

# 3. 重置資料庫
# 在 Supabase Dashboard 執行 supabase_reset_and_init.sql
```

---

### 問題 2: 空白的 Brain 圖譜

**症狀**: Brain 分頁顯示空白

**可能原因**:
1. 沒有日記資料
2. API 查詢失敗
3. D3.js 載入失敗

**解決方案**:
```bash
# 1. 檢查是否有資料
curl http://127.0.0.1:8000/api/v1/memories?limit=5

# 2. 檢查前端 console
# 打開瀏覽器開發者工具 (F12)
# 查看 Console 是否有錯誤

# 3. 先新增一筆日記
# 使用 Capture 分頁新增日記
```

---

### 問題 3: Supabase 表不存在

**症狀**: `Could not find the table 'public.memories'`

**解決方案**:
1. 登入 Supabase Dashboard
2. SQL Editor → New query
3. 複製 `backend-cortex/infra/supabase_reset_and_init.sql`
4. 貼上並執行
5. 驗證 Table Editor 中有 5 個表

---

### 問題 4: AI 分析失敗

**症狀**: INGEST & ANALYZE 沒有反應或報錯

**可能原因**:
1. GOOGLE_API_KEY 未設定或無效
2. Gemini API 配額用完
3. 網路連接問題

**解決方案**:
```bash
# 1. 檢查環境變數
echo $GOOGLE_API_KEY  # Linux/Mac
$env:GOOGLE_API_KEY   # Windows PowerShell

# 2. 測試 API Key
python -c "from google import genai; client = genai.Client(api_key='YOUR_KEY'); print('OK')"

# 3. 檢查配額
# 前往 https://aistudio.google.com/apikey
```

---

## ✅ 測試檢查清單

### 後端測試
- [ ] 後端啟動成功
- [ ] `/health` 端點正常
- [ ] Supabase 連接成功
- [ ] AI 分析功能正常
- [ ] 雙寫策略運作
- [ ] 所有 API 端點正常

### 前端測試
- [ ] 前端啟動成功
- [ ] Capture 分頁正常
- [ ] Brain 分頁顯示圖譜
- [ ] List 分頁顯示列表
- [ ] Projects 分頁可創建專案
- [ ] Dashboard 顯示統計
- [ ] Settings 顯示狀態

### 雲端測試
- [ ] Supabase 寫入成功
- [ ] Supabase 讀取成功
- [ ] Dashboard 可查看資料
- [ ] 資料完整性正確

### 整合測試
- [ ] 完整流程：輸入 → 分析 → 存檔 → 查看
- [ ] 所有分頁可切換
- [ ] 資料在各分頁同步顯示
- [ ] 錯誤處理正常

---

## 🚀 測試通過後的下一步

1. **部署到 Vercel** (前端)
   ```bash
   cd frontend-body
   vercel deploy
   ```

2. **部署後端** (自行選擇平台)
   - Railway
   - Render
   - Fly.io

3. **配置環境變數** (生產環境)
   - GOOGLE_API_KEY
   - SUPABASE_URL
   - SUPABASE_KEY
   - NEXT_PUBLIC_PYTHON_API_URL

4. **測試生產環境**
   - 使用相同的測試流程
   - 驗證所有功能

---

## 📞 需要幫助？

如果測試失敗：
1. 檢查本文檔的「常見問題排查」
2. 查看 `SYSTEM_CONTEXT.md` 的 "Common Pitfalls"
3. 檢查後端 terminal 日誌
4. 檢查前端 browser console
5. 詢問 AI：「測試失敗，錯誤訊息是 XXX」

---

**祝測試順利！** 🎉
