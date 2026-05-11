@echo off
REM Launcher for Accessibility Project Manager (Windows)
cd /d "%~dp0"
where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: 'uv' not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
echo Starting Accessibility Project Manager...
uv run AccessMan
pause
