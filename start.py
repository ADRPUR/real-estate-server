#!/usr/bin/env python3
"""
Start the Real Estate Server
"""
import sys
import subprocess
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"

def main():
    print("=" * 60)
    print("🚀 Starting Real Estate Server")
    print("=" * 60)
    print()

    # Check if venv exists
    if not VENV_PYTHON.exists():
        print("❌ Virtual environment not found!")
        print(f"Expected: {VENV_PYTHON}")
        print()
        print("Please run: python3 -m venv .venv")
        sys.exit(1)

    # Check if package is installed
    result = subprocess.run(
        [str(VENV_PYTHON), "-c", "import app"],
        capture_output=True,
        cwd=PROJECT_ROOT
    )

    if result.returncode != 0:
        print("📦 Package not installed. Installing...")
        install_result = subprocess.run(
            [str(VENV_PYTHON), "-m", "pip", "install", "-e", "."],
            cwd=PROJECT_ROOT
        )
        if install_result.returncode != 0:
            print("❌ Failed to install package")
            sys.exit(1)
        print("✅ Package installed")
        print()

    print("✅ Environment ready")
    print()
    print("📍 Server will start at: http://0.0.0.0:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    print("=" * 60)
    print()

    # Start the server
    try:
        subprocess.run(
            [str(VENV_PYTHON), "main.py"],
            cwd=PROJECT_ROOT
        )
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Server stopped")
        print("=" * 60)

if __name__ == "__main__":
    main()

