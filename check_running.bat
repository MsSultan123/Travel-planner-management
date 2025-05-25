@echo off
echo Checking if Travel Management System is running...

REM Check if python process with app.py is running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq app.py" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Application is running!
) else (
    echo Application is not running. Starting it now...
    call startup.bat
)

pause 