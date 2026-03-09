@echo off
title AI Coach Companion - Setup
echo.
echo  ================================================
echo    AI Coach Companion - One-Click Setup
echo  ================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python not found. Please install Python 3.10+ from python.org
    echo      https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  [1/3] Installing dependencies...
pip install -r requirements.txt -q

echo.
echo  [2/3] Creating data directory...
if not exist "data" mkdir data

echo.
echo  [3/3] Starting AI Coach...
echo.
echo  ================================================
echo    App is starting! Opening in your browser...
echo    Press Ctrl+C to stop.
echo  ================================================
echo.

streamlit run app.py
