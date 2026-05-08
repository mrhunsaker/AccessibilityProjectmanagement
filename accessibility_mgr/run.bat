@echo off
REM Launcher for Braille & Maker Studio — Windows
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

python -c "import textual" >nul 2>&1
if errorlevel 1 (
    echo Installing required library: textual...
    pip install textual -q
)

echo Starting Braille ^& Maker Studio...
python app.py
pause
