@echo off
title Simi-SaveAll - Push to GitHub
cd /d "%~dp0"

REM ============================================================
REM  Simi-SaveAll Video Downloader - Quick Push Script
REM  Usage: push.bat [commit message]
REM  Examples:
REM    push.bat
REM    push.bat "fix Bilibili download bug"
REM ============================================================

echo.
echo ============================================
echo   Simi-SaveAll - Push to GitHub
echo ============================================
echo.

REM Check if inside a git repo
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Not a git repository!
    echo Run this from C:\Users\spiderman\Desktop\Video-Downloader
    pause
    exit /b 1
)

REM Set git user info
git config user.name "simikangtao"
git config user.email "simikangtao@users.noreply.github.com"

REM Ensure remote is set
git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo Setting up remote...
    git remote add origin https://github.com/simikangtao/Simi-SaveAll-Video-Downloader.git
)

REM Show current status
echo --- Git Status ---
git status --short
echo.

REM Get commit message
set MSG=%1
if "%MSG%"=="" (
    echo No commit message provided. Using default message...
    for /f "tokens=* delims=" %%a in ('date /t') do set TODAY=%%a
    set MSG=Update on %TODAY%
)

REM Stage all changes (except .gitignore-excluded files)
echo Staging changes...
git add -A

REM Check if there are changes to commit
git diff --cached --quiet
if %errorlevel% equ 0 (
    echo No changes to commit. Nothing to push.
    pause
    exit /b 0
)

REM Commit
echo Committing: %MSG%
git commit -m "%MSG%"

REM Push to GitHub
echo Pushing to GitHub...
echo (This may take a moment...)
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   SUCCESS! Code pushed to GitHub
    echo   https://github.com/simikangtao/Simi-SaveAll-Video-Downloader
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   PUSH FAILED
    echo   Check your internet connection and try again.
    echo ============================================
)

pause