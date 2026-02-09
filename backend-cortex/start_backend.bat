@echo off
echo ==========================================
echo Starting LifeOS Cortex Backend...
echo ==========================================

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing requirements...
python -m pip install uvicorn
python -m pip install -r requirements.txt

echo Starting server...
echo Access the API documentation at http://127.0.0.1:8000/docs
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

if %errorlevel% neq 0 (
    echo Server failed to start.
    pause
    exit /b %errorlevel%
)

pause
