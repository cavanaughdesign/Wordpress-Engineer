@echo off
echo Installing WordPress Engineer 2...
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or newer.
    echo You can download Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "%~dp0venv" (
    echo Creating virtual environment...
    python -m venv "%~dp0venv"
)

:: Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call "%~dp0venv\Scripts\activate.bat"

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing required packages...
pip install -r "%~dp0requirements.txt"

:: Initialize database if needed
if not exist "%~dp0wp_knowledge.db" (
    echo Creating initial knowledge database...
    python -c "from tools.rag_database import RAGDatabase; RAGDatabase().initialize_db()"
)

echo.
echo Installation completed successfully!
echo To run WordPress Engineer 2, use launch.bat
echo.

pause