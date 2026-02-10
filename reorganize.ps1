# LifeOS 目錄重組腳本
# 將現有結構重組為 AI/使用者/程式 三層分類

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LifeOS 目錄重組工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = "c:\Users\lien.huang\AppData\lifeosjxs"
Set-Location $rootPath

Write-Host "當前目錄: $rootPath" -ForegroundColor Gray
Write-Host ""

# ============================================================================
# Step 1: 創建新目錄結構
# ============================================================================

Write-Host "[1/6] 創建新目錄結構..." -ForegroundColor Yellow

$directories = @(
    "src",
    "src\frontend",
    "src\backend",
    "src\database",
    "docs\for-ai",
    "docs\for-users",
    "docs\archive\fixes",
    "docs\archive\features",
    "docs\archive\sessions",
    "config",
    "data\kernel",
    "data\uploads",
    "data\cache",
    "scripts"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Host "  ✅ 創建 $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  已存在 $dir" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 2: 移動源代碼
# ============================================================================

Write-Host "[2/6] 移動源代碼..." -ForegroundColor Yellow

# 移動前端
if (Test-Path "frontend-body") {
    Write-Host "  - 移動 frontend-body → src/frontend" -ForegroundColor Gray
    Get-ChildItem -Path "frontend-body" | Move-Item -Destination "src\frontend\" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "frontend-body" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 前端代碼已移動" -ForegroundColor Green
}

# 移動後端
if (Test-Path "backend-cortex") {
    Write-Host "  - 移動 backend-cortex → src/backend" -ForegroundColor Gray
    Get-ChildItem -Path "backend-cortex" | Move-Item -Destination "src\backend\" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "backend-cortex" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 後端代碼已移動" -ForegroundColor Green
}

# 移動資料庫
if (Test-Path "database-hippocampus") {
    Write-Host "  - 移動 database-hippocampus → src/database" -ForegroundColor Gray
    Get-ChildItem -Path "database-hippocampus" | Move-Item -Destination "src\database\" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "database-hippocampus" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 資料庫代碼已移動" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 3: 移動 AI 開發者文檔
# ============================================================================

Write-Host "[3/6] 移動 AI 開發者文檔..." -ForegroundColor Yellow

$aiDocs = @(
    "AI_DEV_GUIDE.md",
    "SYSTEM_CONTEXT.md",
    "QUESTION_DRIVEN_ARCHITECTURE.md",
    "C_KERNEL_GUIDE.md"
)

foreach ($doc in $aiDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\for-ai\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/for-ai/" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 4: 移動使用者文檔
# ============================================================================

Write-Host "[4/6] 移動使用者文檔..." -ForegroundColor Yellow

$userDocs = @(
    "USER_MANUAL.md"
)

foreach ($doc in $userDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\for-users\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/for-users/" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 5: 移動歷史文檔
# ============================================================================

Write-Host "[5/6] 移動歷史文檔..." -ForegroundColor Yellow

# 修復記錄
$fixDocs = @(
    "MOBILE_DRAG_FIX.md",
    "EMBEDDING_MODEL_FIX.md",
    "CORTEXCHAT_CONNECTION_FIX.md",
    "RUNTIME_ERROR_FIX.md",
    "ANALYSIS_DISPLAY_FIX.md",
    "UI_FIX_CAPTUREVIEW.md",
    "FIX_SUMMARY.md",
    "ERROR_RESOLUTION_REPORT.txt",
    "QUICK_FIX.md"
)

foreach ($doc in $fixDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\archive\fixes\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/archive/fixes/" -ForegroundColor Green
    }
}

# 功能記錄
$featureDocs = @(
    "CARD_STACK_DASHBOARD.md",
    "CARD_STACK_QUICK_START.md",
    "AI_FLOATING_ASSISTANT_UPDATE.md",
    "MEDIA_CORE_ARCHITECTURE.h",
    "MEDIA_CORE_INTEGRATION.md",
    "MEDIA_CORE_NOMAD_SUMMARY.md",
    "NOMAD_LIST_STYLE_DESIGN.md"
)

foreach ($doc in $featureDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\archive\features\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/archive/features/" -ForegroundColor Green
    }
}

# 會話記錄
$sessionDocs = @(
    "SESSION_COMPLETE_SUMMARY.md",
    "CONTEXT_ENGINEERING_COMPLETE.md",
    "CONTEXT_ENGINEERING_GUIDE.md",
    "CONTEXT_ENGINEERING_QUICKSTART.md"
)

foreach ($doc in $sessionDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\archive\sessions\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/archive/sessions/" -ForegroundColor Green
    }
}

# 其他文檔
$otherDocs = @(
    "README_DOCS.md",
    "CLEANUP_PLAN.md",
    "DIRECTORY_STRUCTURE_DESIGN.md"
)

foreach ($doc in $otherDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ $doc → docs/" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 6: 移動配置和腳本
# ============================================================================

Write-Host "[6/6] 移動配置和腳本..." -ForegroundColor Yellow

# 移動配置
if (Test-Path ".cursorrules") {
    Copy-Item -Path ".cursorrules" -Destination "config\" -Force
    Write-Host "  ✅ .cursorrules → config/ (保留根目錄副本)" -ForegroundColor Green
}

if (Test-Path ".env.shared") {
    Move-Item -Path ".env.shared" -Destination "config\" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ .env.shared → config/" -ForegroundColor Green
}

# 移動腳本
if (Test-Path "cleanup.ps1") {
    Move-Item -Path "cleanup.ps1" -Destination "scripts\" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ cleanup.ps1 → scripts/" -ForegroundColor Green
}

# 移動編譯腳本
if (Test-Path "src\backend\kernel\compile.bat") {
    Copy-Item -Path "src\backend\kernel\compile.bat" -Destination "scripts\" -Force
    Write-Host "  ✅ compile.bat → scripts/ (保留 kernel 目錄副本)" -ForegroundColor Green
}

if (Test-Path "src\backend\kernel\compile.sh") {
    Copy-Item -Path "src\backend\kernel\compile.sh" -Destination "scripts\" -Force
    Write-Host "  ✅ compile.sh → scripts/ (保留 kernel 目錄副本)" -ForegroundColor Green
}

# 移動 C Kernel 資料
if (Test-Path "src\backend\kernel\storage") {
    Write-Host "  - 移動 kernel storage → data/kernel" -ForegroundColor Gray
    Get-ChildItem -Path "src\backend\kernel\storage" -File | Move-Item -Destination "data\kernel\" -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ Kernel 資料已移動" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# 完成
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "重組完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "新目錄結構：" -ForegroundColor Yellow
Write-Host ""
Write-Host "📂 src/              - 程式源代碼" -ForegroundColor White
Write-Host "   ├── frontend/     - 前端代碼" -ForegroundColor Gray
Write-Host "   ├── backend/      - 後端代碼" -ForegroundColor Gray
Write-Host "   └── database/     - 資料庫" -ForegroundColor Gray
Write-Host ""
Write-Host "📂 docs/             - 文檔中心" -ForegroundColor White
Write-Host "   ├── for-ai/       - AI 開發者文檔" -ForegroundColor Gray
Write-Host "   ├── for-users/    - 使用者文檔" -ForegroundColor Gray
Write-Host "   └── archive/      - 歷史文檔" -ForegroundColor Gray
Write-Host ""
Write-Host "📂 config/           - 配置文件" -ForegroundColor White
Write-Host "📂 data/             - 資料目錄" -ForegroundColor White
Write-Host "📂 scripts/          - 工具腳本" -ForegroundColor White
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "下一步" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 更新 package.json 中的路徑" -ForegroundColor Yellow
Write-Host "2. 更新 Python 代碼中的相對路徑" -ForegroundColor Yellow
Write-Host "3. 測試前端和後端是否正常運行" -ForegroundColor Yellow
Write-Host "4. 提交到 Git" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ 重組完成！" -ForegroundColor Green
