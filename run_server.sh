#!/bin/bash
# Script pentru pornirea serverului Real Estate

set -e  # Exit on error

echo "🚀 Starting Real Estate Server..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Activate venv
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if ! python -c "import fastapi, xlrd, requests, apscheduler" 2>/dev/null; then
    echo "📥 Installing/updating dependencies..."
    pip install -e .
    echo "✅ Dependencies installed"
else
    echo "✅ All dependencies already installed"
fi

# Add src to PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

echo "✅ Environment ready"
echo ""
echo "Starting server at http://0.0.0.0:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python main.py

