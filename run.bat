@echo off
title NexusSocial - Social Media Database & Web App
echo ========================================================
echo   Launching NexusSocial (Social Media Database Project)
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b
)

echo Starting web server on http://localhost:5000 ...
start http://localhost:5000
python app.py
pause
