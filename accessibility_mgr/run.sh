#!/usr/bin/env bash
# Launcher for Braille & Maker Studio Project Manager
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Please install Python 3.9+."
    exit 1
fi

# Check/install textual
if ! python3 -c "import textual" &>/dev/null; then
    echo "Installing required library: textual..."
    pip install textual --break-system-packages -q
fi

echo "Starting Braille & Maker Studio..."
cd "$SCRIPT_DIR"
exec python3 app.py "$@"
