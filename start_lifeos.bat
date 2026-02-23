@echo off
SETLOCAL EnableDelayedExpansion
TITLE LifeOS v7.1 Launch System
COLOR 0A

:: Initialize base directory
set "BASE_DIR=%~dp0"
if "!BASE_DIR:~-1!"=="\" set "BASE_DIR=!BASE_DIR:~0,-1!"

echo ========================================================
echo   LifeOS v7.1 - Cortex ^& Body Activation Protocol
echo ========================================================
echo.

echo [1/4] Terminating Ghost Processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1
echo       - Port 8000 (Backend) Cleared.
echo       - Port 3000 (Frontend) Cleared.
echo.

echo [2/4] Awakening Cortex (Backend)...
pushd "!BASE_DIR!\backend-cortex"
if exist "..\.venv\Scripts\activate.bat" (
    echo       - Virtual environment detected. Activating...
    start "LifeOS Cortex" cmd /k "..\.venv\Scripts\activate.bat && python main.py"
) else if exist "venv\Scripts\activate.bat" (
    echo       - Local venv found. Activating...
    start "LifeOS Cortex" cmd /k "venv\Scripts\activate.bat && python main.py"
) else (
    echo       - [WARN] No venv found. Falling back to global python.
    start "LifeOS Cortex" cmd /k "python main.py"
)
popd
timeout /t 5 >nul
echo       - Cortex Signal Active.
echo.

echo [3/4] Materializing Body (Frontend)...
pushd "!BASE_DIR!\frontend-body"
echo       - Checking for Node.js...
where node >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    start "LifeOS Body" cmd /k "npm run dev"
    echo       - Body Synthesis Initiated.
) else (
    echo       - [ERROR] Node.js/npm not found in PATH!
    echo       - Searching for common installation paths...
    if exist "C:\Program Files\nodejs\node.exe" (
        echo       - Found Node.js in Program Files. Adding to session PATH...
        set "PATH=%PATH%;C:\Program Files\nodejs"
        start "LifeOS Body" cmd /k "npm run dev"
        echo       - Body Synthesis Initiated with local PATH calibration.
    ) else (
        echo       - [CRITICAL] Node.js is NOT installed or cannot be found.
        echo       - Please install Node.js from: https://nodejs.org/
        pause
    )
)
popd
echo.

echo [4/4] Establishing Neural Link...
timeout /t 5 >nul
start http://localhost:3000
echo.

echo ========================================================
echo   SYSTEM ONLINE.
echo   - Backend: http://127.0.0.1:8000
echo   - Frontend: http://localhost:3000
echo.
echo   Keep popup windows open. Minimizing them is fine.
echo ========================================================
pause
