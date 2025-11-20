#!/usr/bin/env python3
"""
Generate coverage badge and update README if needed.
Run this after tests to update the coverage badge.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Generate coverage report and badge."""
    print("🧪 Running tests with coverage...")

    # Run tests with coverage
    result = subprocess.run(
        ["pytest", "--cov=app", "--cov-report=xml", "--cov-report=html", "--cov-report=term"],
        cwd=Path(__file__).parent
    )

    if result.returncode != 0:
        print("❌ Tests failed!")
        sys.exit(1)

    print("\n✅ Tests passed!")
    print("\n📊 Generating coverage badge...")

    # Generate badge
    badge_result = subprocess.run(
        ["coverage-badge", "-o", "coverage.svg", "-f"],
        cwd=Path(__file__).parent
    )

    if badge_result.returncode == 0:
        print("✅ Coverage badge generated: coverage.svg")
        print("📄 HTML report available in: htmlcov/index.html")
    else:
        print("⚠️  Failed to generate badge. Install coverage-badge:")
        print("    pip install coverage-badge")
        sys.exit(1)

if __name__ == "__main__":
    main()

