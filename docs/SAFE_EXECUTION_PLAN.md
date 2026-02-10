# LifeOS 安全清理與重組方案
**確保不影響開發的執行計劃**

---

## ✅ 安全檢查清單

### 1. 不會刪除的內容（100% 安全）
- ✅ 所有源代碼（frontend-body, backend-cortex, database-hippocampus）
- ✅ node_modules/（開發依賴）
- ✅ .git/（版本控制）
- ✅ 配置文件（.cursorrules, .env.shared, package.json, tsconfig.json 等）
- ✅ README.md

### 2. 會刪除的內容（可重新生成）
- ❌ .next/（124 MB）- 執行 `npm run build` 可重新生成
- ❌ backend-cortex/venv/（300 MB）- 執行 `pip install -r requirements.txt` 可重新創建
- ❌ __pycache__/（5 MB）- Python 自動生成

### 3. 會移動的內容（只是換位置）
- 📁 文檔移到 docs/ 目錄
- 📁 源代碼移到 src/ 目錄
- 📁 配置移到 config/ 目錄

---

## 🔒 開發環境保護

### 執行前
```
frontend-body/
├── app/              ✅ 保留
├── components/       ✅ 保留
├── lib/              ✅ 保留
├── node_modules/     ✅ 保留
├── package.json      ✅ 保留
└── .next/            ❌ 刪除（可重新生成）

backend-cortex/
├── routers/          ✅ 保留
├── kernel/           ✅ 保留
├── main.py           ✅ 保留
├── requirements.txt  ✅ 保留
├── venv/             ❌ 刪除（可重新創建）
└── __pycache__/      ❌ 刪除（自動生成）
```

### 執行後
```
src/frontend/         ✅ 所有源代碼完整保留
src/backend/          ✅ 所有源代碼完整保留
node_modules/         ✅ 保留
```

---

## 🚀 執行步驟（分階段，可隨時停止）

### Phase 1: 只清理（最安全）
```powershell
# 只刪除編譯產物，不移動任何文件
.\cleanup.ps1
```

**影響**：
- ✅ 節省 430 MB 空間
- ✅ 不影響開發
- ✅ 可隨時重新生成

**恢復方法**：
```bash
# 前端
cd frontend-body
npm run build

# 後端
cd backend-cortex
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Phase 2: 重組目錄（需要更新路徑）
```powershell
# 移動文件到新目錄結構
.\reorganize.ps1
```

**影響**：
- ⚠️ 需要更新 import 路徑
- ⚠️ 需要更新配置文件

**建議**：先不執行，等確認 Phase 1 沒問題後再執行

---

## 📋 執行確認

### 我建議分兩步執行：

#### Step 1: 先執行清理（現在）
```powershell
.\cleanup.ps1
```

**這一步 100% 安全**：
- ✅ 只刪除可重新生成的文件
- ✅ 不移動任何源代碼
- ✅ 不影響開發
- ✅ 節省 430 MB

#### Step 2: 等測試沒問題後，再執行重組（稍後）
```powershell
.\reorganize.ps1
```

**這一步需要更新路徑**：
- ⚠️ 需要更新 package.json
- ⚠️ 需要更新 Python import
- ⚠️ 建議在 Git commit 後執行

---

## ✅ 現在執行 Phase 1（清理）

**確認執行清理腳本？**

這將：
1. 刪除 .next/（124 MB）
2. 刪除 backend-cortex/venv/（300 MB）
3. 刪除 __pycache__/（5 MB）
4. 整理文檔到 docs/ 目錄

**不會影響**：
- ✅ 所有源代碼
- ✅ node_modules/
- ✅ 開發環境

**準備好了嗎？**
