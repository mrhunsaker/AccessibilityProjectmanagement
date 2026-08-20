@echo off
:: Accessibility Project Management - Setup Script for Windows
:: This script launches the Python setup assistant

:: Get the directory of this script
set "SCRIPT_DIR=%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found in PATH
    echo Please install Python 3.12+ and ensure it's in your PATH
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2 delims=: " %%v in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do (
    set PY_MAJOR=%%v
)
for /f "tokens=3 delims=: " %%v in ('python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2^>nul') do (
    set PY_MINOR=%%v
)

if %PY_MAJOR% LSS 3 (
    echo Error: Python 3.12 or higher is required
    pause
    exit /b 1
)

if %PY_MAJOR% EQU 3 (
    if %PY_MINOR% LSS 12 (
        echo Error: Python 3.12 or higher is required (found: 3.%PY_MINOR%)
        pause
        exit /b 1
    )
)

:: Run the setup assistant
cd /d "%SCRIPT_DIR%"
python setup.py
