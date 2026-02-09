@echo off
echo ==========================================
echo Starting LifeOS Body Frontend...
echo ==========================================

cd /d "%~dp0"

set NODE_HOME=c:\Users\lien.huang\AppData\node
set PATH=%NODE_HOME%;%PATH%

if not exist node_modules (
    echo Installing dependencies...
    call "%NODE_HOME%\npm.cmd" install
)

echo Starting development server...
echo Access the application at http://localhost:3000
call "%NODE_HOME%\npm.cmd" run dev

pause
