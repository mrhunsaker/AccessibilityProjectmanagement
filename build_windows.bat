@echo off
REM Build AccessMan for Windows
REM Usage: build_windows.bat

setlocal

cd /d %~dp0

REM Create output directories
if not exist dist\windows mkdir dist\windows
if not exist build\windows mkdir build\windows

REM Set environment for browser-only mode
set NICEGUI_BROWSER_ONLY=1

REM Build with PyInstaller
python -m PyInstaller ^
    accessibility_mgr/app.py ^
    --onefile ^
    --name=AccessMan ^
    --add-data="accessibility_mgr/resources;accessibility_mgr/resources" ^
    --add-data="accessibility_mgr/db;accessibility_mgr/db" ^
    --hidden-import=nicegui ^
    --hidden-import=sqlalchemy ^
    --hidden-import=cryptography ^
    --hidden-import=cryptography.fernet ^
    --hidden-import=accessibility_mgr ^
    --clean ^
    --distpath=dist/windows ^
    --workpath=build/windows ^
    --icon=accessibility_mgr/resources/icons/favicon.ico

echo ✅ Windows build complete: dist\windows\AccessMan.exe
echo    To run: dist\windows\AccessMan.exe
pause
