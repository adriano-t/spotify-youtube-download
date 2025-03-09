@echo off
setlocal enabledelayedexpansion

:: Check if FFmpeg is already installed
where ffmpeg >nul 2>nul
if %errorlevel% == 0 (
    echo FFmpeg is already installed and present in the PATH.
    exit /b
)

echo FFmpeg not found. Installing...

:: Set variables
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "DEST_FOLDER=%USERPROFILE%\ffmpeg"
set "ZIP_FILE=%TEMP%\ffmpeg.zip"

:: Download FFmpeg
powershell -Command "& {Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%ZIP_FILE%'}"

:: Verify download
if not exist "%ZIP_FILE%" (
    echo Download failed! Exiting...
    exit /b
)

:: Create destination folder
if not exist "%DEST_FOLDER%" mkdir "%DEST_FOLDER%"

:: Extract FFmpeg
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%DEST_FOLDER%' -Force"

:: Verify extraction
if not exist "%DEST_FOLDER%\ffmpeg-*\" (
    echo Extraction failed! Exiting...
    exit /b
)

:: Find the bin folder
for /d %%D in ("%DEST_FOLDER%\ffmpeg-*") do set "BIN_FOLDER=%%D\bin"

:: Verify bin folder
if not exist "!BIN_FOLDER!\ffmpeg.exe" (
    echo FFmpeg binary not found! Exiting...
    exit /b
)

:: Add FFmpeg to PATH
setx PATH "!BIN_FOLDER!;%PATH%" /M

:: Cleanup
if exist "%ZIP_FILE%" del "%ZIP_FILE%"

echo FFmpeg successfully installed in %DEST_FOLDER% and added to PATH.

:: Install required Python packages
if exist "requirements.txt" (
    echo Installing required Python packages...
    pip install -r requirements.txt
) else (
    echo The file requirements.txt does not exist.
)

pause
