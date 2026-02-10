# LifeOS 清理執行腳本
# 自動清理不必要的文件和目錄

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LifeOS 目錄清理工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = "c:\Users\lien.huang\AppData\lifeosjxs"
Set-Location $rootPath

# ============================================================================
# Step 1: 刪除編譯產物和緩存
# ============================================================================

Write-Host "[1/5] 刪除編譯產物和緩存..." -ForegroundColor Yellow

# 刪除 .next (124.74 MB)
if (Test-Path ".next") {
    Write-Host "  - 刪除 .next/ (124.74 MB)..." -ForegroundColor Gray
    Remove-Item -Path ".next" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 已刪除 .next/" -ForegroundColor Green
}

# 刪除 Python 緩存
Write-Host "  - 刪除 Python 緩存..." -ForegroundColor Gray
Get-ChildItem -Path "backend-cortex" -Recurse -Include "__pycache__","*.pyc","*.pyo" -ErrorAction SilentlyContinue | 
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  ✅ 已刪除 Python 緩存" -ForegroundColor Green

# 刪除 Python 虛擬環境 (venv) - 這是最大的問題！
if (Test-Path "backend-cortex\venv") {
    Write-Host "  - 刪除 backend-cortex\venv/ (約 300 MB)..." -ForegroundColor Gray
    Remove-Item -Path "backend-cortex\venv" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 已刪除 venv/ (可用 pip install -r requirements.txt 重新創建)" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 2: 創建 docs 目錄
# ============================================================================

Write-Host "[2/5] 創建 docs 目錄結構..." -ForegroundColor Yellow

if (-not (Test-Path "docs")) {
    New-Item -Path "docs" -ItemType Directory | Out-Null
    Write-Host "  ✅ 創建 docs/" -ForegroundColor Green
}

if (-not (Test-Path "docs\archive")) {
    New-Item -Path "docs\archive" -ItemType Directory | Out-Null
    Write-Host "  ✅ 創建 docs/archive/" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# Step 3: 移動核心文檔
# ============================================================================

Write-Host "[3/5] 移動核心文檔到 docs/..." -ForegroundColor Yellow

$coreDocsmd = @(
    "AI_DEV_GUIDE.md",
    "USER_MANUAL.md",
    "C_KERNEL_GUIDE.md",
    "SYSTEM_CONTEXT.md",
    "QUESTION_DRIVEN_ARCHITECTURE.md",
    "README_DOCS.md",
    "CLEANUP_PLAN.md"
)

foreach ($doc in $coreDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ 移動 $doc" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 4: 移動歷史文檔到 archive
# ============================================================================

Write-Host "[4/5] 移動歷史文檔到 docs/archive/..." -ForegroundColor Yellow

$archiveDocs = @(
    "AI_FLOATING_ASSISTANT_UPDATE.md",
    "ANALYSIS_DISPLAY_FIX.md",
    "CARD_STACK_DASHBOARD.md",
    "CARD_STACK_QUICK_START.md",
    "CONTEXT_ENGINEERING_COMPLETE.md",
    "CONTEXT_ENGINEERING_GUIDE.md",
    "CONTEXT_ENGINEERING_QUICKSTART.md",
    "CORTEXCHAT_CONNECTION_FIX.md",
    "EMBEDDING_MODEL_FIX.md",
    "ERROR_RESOLUTION_REPORT.txt",
    "FIX_SUMMARY.md",
    "MEDIA_CORE_ARCHITECTURE.h",
    "MEDIA_CORE_INTEGRATION.md",
    "MEDIA_CORE_NOMAD_SUMMARY.md",
    "MOBILE_DRAG_FIX.md",
    "NOMAD_LIST_STYLE_DESIGN.md",
    "QUICK_FIX.md",
    "RUNTIME_ERROR_FIX.md",
    "SESSION_COMPLETE_SUMMARY.md",
    "UI_FIX_CAPTUREVIEW.md"
)

foreach ($doc in $archiveDocs) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs\archive\" -Force -ErrorAction SilentlyContinue
        Write-Host "  ✅ 移動 $doc" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================================
# Step 5: 顯示清理結果
# ============================================================================

Write-Host "[5/5] 清理完成！" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "清理結果" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 計算目錄大小
$dirs = @("frontend-body", "backend-cortex", "node_modules", "docs")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        $size = (Get-ChildItem $dir -Recurse -ErrorAction SilentlyContinue | 
                 Measure-Object -Property Length -Sum).Sum / 1MB
        $sizeRounded = [math]::Round($size, 2)
        Write-Host "$dir : $sizeRounded MB" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "下一步" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 如需重新安裝 Python 依賴：" -ForegroundColor Yellow
Write-Host "   cd backend-cortex" -ForegroundColor Gray
Write-Host "   python -m venv venv" -ForegroundColor Gray
Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 如需重新編譯前端：" -ForegroundColor Yellow
Write-Host "   cd frontend-body" -ForegroundColor Gray
Write-Host "   npm run build" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 核心文檔已移到 docs/ 目錄" -ForegroundColor Yellow
Write-Host "   歷史文檔已移到 docs/archive/ 目錄" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ 清理完成！" -ForegroundColor Green
