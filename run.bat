@echo off
REM Friday AI v3 - Python Version
REM Windows Launcher - No Node.js Required!

setlocal enabledelayedexpansion

echo.
echo ========================================
echo    Friday AI v3 - Python Edition
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo ERROR: Python is not installed!
    echo.
    echo Please download and install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python is installed - Good!
echo.

REM Check if Ollama is running
echo Checking Ollama service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo WARNING: Ollama is not running!
    echo.
    echo Please download and install Ollama from:
    echo https://ollama.ai
    echo.
    echo After installing and starting Ollama, run this file again.
    echo.
    pause
    exit /b 1
)

echo Ollama is running - Good!
echo.

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo ERROR: Failed to install dependencies
    echo.
    pause
    exit /b 1
)

echo.
echo Starting Friday AI on http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask app
python app.py

pause
