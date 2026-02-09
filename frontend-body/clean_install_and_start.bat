@echo off
echo ==========================================
echo CLEAN INSTALL REPAIR TOOL
echo ==========================================

cd /d "%~dp0"

echo 1. Setting Node Path...
set NODE_HOME=c:\Users\lien.huang\AppData\node
set PATH=%NODE_HOME%;%PATH%

echo 2. Cleaning old files (this might take a moment)...
if exist .next (
    rmdir /s /q .next
    echo    - Deleted .next cache
)
if exist node_modules (
    rmdir /s /q node_modules
    echo    - Deleted node_modules
)
if exist package-lock.json (
    del package-lock.json
    echo    - Deleted package-lock.json
)

echo 3. Installing dependencies with explicit NPM path...
echo    Running: "%NODE_HOME%\npm.cmd" install
call "%NODE_HOME%\npm.cmd" install

echo 4. Verifying Zustand...
if exist node_modules\zustand (
    echo    - [SUCCESS] Zustand is present.
) else (
    echo    - [ERROR] Zustand is STILL missing. Check your network or permissions.
    pause
    exit /b 1
)

echo 5. Starting Dev Server...
echo    Access at http://localhost:3000
call "%NODE_HOME%\npm.cmd" run dev

pause
