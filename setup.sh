#!/bin/bash
# Accessibility Project Management - Setup Script
# This script launches the Python setup assistant

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python 3.12+ is available
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python 3.12 or higher is required but not found."
    echo "Please install Python 3.12+ and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
if [[ "$PYTHON_VERSION" < "3.12" ]]; then
    echo "Error: Python 3.12 or higher is required (found: $PYTHON_VERSION)."
    exit 1
fi

# Run the setup assistant
cd "$SCRIPT_DIR"
exec $PYTHON_CMD setup.py
