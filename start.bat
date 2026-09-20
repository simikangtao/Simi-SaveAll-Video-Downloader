@echo off
title Simi-SaveAll - Video Downloader
cd /d "%~dp0"

echo ============================================
echo   Simi-SaveAll - Video Downloader
echo ============================================
echo.

REM Kill any old Python server on port 3000
echo [1/3] Checking for existing servers on port 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    echo -- Killing old process PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
if %errorlevel%==0 echo -- Port 3000 is now free
timeout /t 2 /nobreak >nul

REM Kill any old python.exe that was running app.py from this folder
echo [2/3] Starting server...
echo.
echo  Press Ctrl+C to stop the server
echo.

REM Start the server
python app.py

pause