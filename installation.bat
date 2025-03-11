@echo off
setlocal enabledelayedexpansion

:: Install required Python packages
if exist "requirements.txt" (
    echo Installing required Python packages...
    pip install -r requirements.txt
) else (
    echo The file requirements.txt does not exist.
)

pause
