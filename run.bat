@echo off
echo Setting up Travel Management System...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python init_db.py

REM Start the application
echo Starting the application...
python app.py

pause 