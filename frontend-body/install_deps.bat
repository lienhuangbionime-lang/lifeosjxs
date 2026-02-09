@echo off
echo ==========================================
echo Force Re-installing Frontend Dependencies...
echo ==========================================

cd /d "%~dp0"

set NODE_HOME=c:\Users\lien.huang\AppData\node
set PATH=%NODE_HOME%;%PATH%

echo Using Node from: %NODE_HOME%
node -v
npm -v

echo Installing 'zustand' explicitly...
call "%NODE_HOME%\npm.cmd" install zustand

echo Verifying installation...
if exist node_modules\zustand (
    echo [SUCCESS] Zustand installed.
) else (
    echo [ERROR] Zustand installation failed.
    pause
    exit /b 1
)

echo Done.
pause
