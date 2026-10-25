@echo off
title EverythingWithAI Server
cd /d "%~dp0"
echo ========================================================
echo   Starting EverythingWithAI Server...
echo ========================================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server exited with error code %ERRORLEVEL%.
    echo Please make sure dependencies are installed: pip install -r requirements.txt
    pause
)
