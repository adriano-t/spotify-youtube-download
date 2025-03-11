@echo off
:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3 and try again.
    pause
    exit /b
)

python spotify-export-liked.py

python spotify-youtube-download.py 1
pause
