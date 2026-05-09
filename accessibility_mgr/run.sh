#!/usr/bin/env bash
# Launcher for Accessibility Materials Project Manager
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv &>/dev/null; then
    echo "ERROR: 'uv' not found. Install it from https://docs.astral.sh/uv/"
    exit 1
fi

echo "Starting Accessibility Materials Project Manager..."
exec uv run AccessMan "$@"
