@echo off
echo Starting Travel Management System at %time% on %date% >> startup.log

REM Change to the script's directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH >> startup.log
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist .venv (
    echo Creating virtual environment... >> startup.log
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment >> startup.log
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment >> startup.log
    exit /b 1
)

REM Install requirements if needed
if exist requirements.txt (
    pip install -r requirements.txt >> startup.log 2>&1
)

REM Check if app.py exists
if not exist app.py (
    echo Error: app.py not found >> startup.log
    exit /b 1
)

REM Kill any existing Python processes (optional, comment out if not needed)
taskkill /F /IM python.exe >nul 2>&1

REM Set Flask environment variables
set FLASK_APP=app.py
set FLASK_ENV=production
set FLASK_DEBUG=0

REM Start the application in background with explicit host and port
echo Starting application... >> startup.log
start /B "" python -m flask run --host=0.0.0.0 --port=5000 >> app.log 2>&1

REM Wait a few seconds to check if the application started successfully
timeout /t 5 /nobreak > nul

REM Check if the application is responding
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000' -UseBasicParsing; if ($response.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Application started successfully at %time% >> startup.log
) else (
    echo Error: Application failed to start or is not responding >> startup.log
    exit /b 1
) 