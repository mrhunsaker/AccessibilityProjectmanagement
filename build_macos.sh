#!/bin/bash
# Build AccessMan for macOS
# Usage: chmod +x build_macos.sh && ./build_macos.sh

set -e

cd "$(dirname "$0")"

mkdir -p dist/macos build/macos

export NICEGUI_BROWSER_ONLY=1

python -m PyInstaller \
    accessibility_mgr/app.py \
    --onefile \
    --name=AccessMan \
    --add-data="resources/icons:resources/icons" \
    --add-data="accessibility_mgr/db:accessibility_mgr/db" \
    --collect-submodules=accessibility_mgr \
    --hidden-import=nicegui \
    --hidden-import=sqlalchemy \
    --hidden-import=cryptography \
    --hidden-import=cryptography.fernet \
    --hidden-import=accessibility_mgr \
    --clean \
    --distpath=dist/macos \
    --workpath=build/macos \
    --windowed

echo "✅ macOS build complete: dist/macos/AccessMan"
echo "   To run: ./dist/macos/AccessMan"
