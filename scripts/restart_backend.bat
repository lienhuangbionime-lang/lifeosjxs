@echo off
echo Restarting LifeOS Backend Cortex...
echo.

REM Kill existing Python processes running uvicorn
echo Stopping existing backend processes...
taskkill /F /FI "WINDOWTITLE eq backend-cortex*" 2>nul
timeout /t 2 /nobreak >nul

REM Start backend server
echo Starting backend server...
cd /d "%~dp0"
start "backend-cortex" cmd /k "python -m uvicorn main:app --reload --port 8000"

echo.
echo Backend server is starting...
echo Access at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
