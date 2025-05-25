@echo off
echo Setting up Travel Management System...

:: Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Install requirements
echo Installing requirements...
pip install -r requirements.txt

:: Initialize the database
echo Initializing database...
python init_db.py

:: Create a sample .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    echo SECRET_KEY=your_secret_key_here > .env
    echo DATABASE_URL=sqlite:///travel.db >> .env
    echo MAIL_SERVER=smtp.gmail.com >> .env
    echo MAIL_PORT=587 >> .env
    echo MAIL_USE_TLS=True >> .env
    echo MAIL_USERNAME=your_email@gmail.com >> .env
    echo MAIL_PASSWORD=your_app_password >> .env
    echo FLASK_APP=app.py >> .env
    echo FLASK_ENV=development >> .env
)

:: Start the application
echo Starting the application...
python app.py 