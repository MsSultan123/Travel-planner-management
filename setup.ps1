Write-Host "Setting up Travel Management System..." -ForegroundColor Green

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Install requirements
Write-Host "Installing requirements..." -ForegroundColor Yellow
pip install -r requirements.txt

# Initialize the database
Write-Host "Initializing database..." -ForegroundColor Yellow
python init_db.py

# Create a sample .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///travel.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
FLASK_APP=app.py
FLASK_ENV=development
"@ | Out-File -FilePath ".env" -Encoding UTF8
}

# Start the application
Write-Host "Starting the application..." -ForegroundColor Green
python app.py 