@echo off
echo Starting Support & Payment Tray Application at %time% on %date% >> tray_startup.log

REM Change to the script's directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH >> tray_startup.log
    exit /b 1
)

REM Check if virtual environment exists, create if not
if not exist .venv (
    echo Creating virtual environment... >> tray_startup.log
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment >> tray_startup.log
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment >> tray_startup.log
    exit /b 1
)

REM Install requirements if needed
if exist requirements.txt (
    pip install -r requirements.txt >> tray_startup.log 2>&1
)

REM Install additional required packages
pip install pystray pillow >> tray_startup.log 2>&1

REM Start the tray application in background
echo Starting tray application... >> tray_startup.log
start /B "" python tray_app.py >> tray_app.log 2>&1

REM Wait a few seconds to check if the application started successfully
timeout /t 5 /nobreak > nul

REM Check if python process is running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq tray_app.py" 2>NUL | find /I /N "python.exe">NUL
if %ERRORLEVEL% EQU 0 (
    echo Tray application started successfully at %time% >> tray_startup.log
) else (
    echo Error: Tray application failed to start >> tray_startup.log
    exit /b 1
) 