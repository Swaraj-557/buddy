@echo off
echo Buddy System - Windows Launcher
echo ================================

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    python -m venv .venv
    
    echo Installing required packages...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install pywin32 requests
)

echo Starting Buddy Server (Windows version)...
.venv\Scripts\python.exe buddy_server_windows.py

pause
