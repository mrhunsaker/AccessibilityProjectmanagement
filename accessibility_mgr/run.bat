@echo off
REM Launcher for Accessibility Materials Project Manager - Windows
cd /d "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: 'uv' not found. Install it from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

echo Starting Accessibility Materials Project Manager...
uv run AccessMan
pause
