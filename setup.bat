@echo off
echo ========================================
echo   Video Downloader Setup Script
echo ========================================
echo.

echo [1/3] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)
echo OK - Node.js installed

echo.
echo [2/3] Installing npm dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo OK - Dependencies installed

echo.
echo [3/3] Checking yt-dlp installation...
yt-dlp --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: yt-dlp not found!
    echo.
    echo Please install yt-dlp manually:
    echo   Option 1: pip install yt-dlp
    echo   Option 2: Download from https://github.com/yt-dlp/yt-dlp/releases
    echo.
) else (
    echo OK - yt-dlp installed
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start the server, run:
echo   npm start
echo.
pause
