@echo off
REM setup.bat - Windows setup script for Invoice Processing System

echo Setting up Invoice Processing System on Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is required but not installed.
    echo Please install Python from https://python.org
    pause
    exit /b 1
)



REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

REM Setup environment file


REM Create database
echo Setting up database...
python -c "from app import app, db; app.app_context().push(); db.create_all()"

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your credentials
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python app.py
echo 4. Open http://localhost:5000

pause