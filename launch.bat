@echo off
echo Starting WordPress Engineer 2...
echo.

:: Check if virtual environment exists
if not exist "%~dp0venv" (
    echo Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

:: Activate virtual environment
call "%~dp0venv\Scripts\activate.bat"

:: Run the application
python "%~dp0main.py"

:: Deactivate virtual environment on exit
call "%~dp0venv\Scripts\deactivate.bat"

pause