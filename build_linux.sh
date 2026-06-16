#!/bin/bash
# Build AccessMan for Linux
# Usage: chmod +x build_linux.sh && ./build_linux.sh

set -e

# Ensure we're in the project root
cd "$(dirname "$0")"

# Create output directories
mkdir -p dist/linux build/linux

# Set environment for browser-only mode
export NICEGUI_BROWSER_ONLY=1

# Build with PyInstaller
python -m PyInstaller \
    accessibility_mgr/app.py \
    --onefile \
    --name=AccessMan \
    --add-data="accessibility_mgr/resources:accessibility_mgr/resources" \
    --add-data="accessibility_mgr/db:accessibility_mgr/db" \
    --hidden-import=nicegui \
    --hidden-import=sqlalchemy \
    --hidden-import=cryptography \
    --hidden-import=cryptography.fernet \
    --hidden-import=accessibility_mgr \
    --clean \
    --distpath=dist/linux \
    --workpath=build/linux

echo "✅ Linux build complete: dist/linux/AccessMan"
echo "   To run: ./dist/linux/AccessMan"
