#!/bin/bash
# Quick setup script for development environment

set -e

echo "🚀 Real Estate Calculator API - Development Setup"
echo "=================================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.11" ]]; then
    echo "❌ Python 3.11+ is required"
    exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

# Install package in editable mode
echo ""
echo "📦 Installing package..."
pip install -e . -q
echo "✓ Package installed"

# Install development dependencies
echo ""
echo "📦 Installing development dependencies..."
pip install -e ".[dev]" -q
echo "✓ Development dependencies installed"

# Install Playwright
echo ""
echo "🎭 Installing Playwright..."
pip install playwright -q
playwright install chromium
echo "✓ Playwright installed"

# Setup pre-commit hooks (optional)
read -p "📝 Install pre-commit hooks? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install pre-commit -q
    pre-commit install
    echo "✓ Pre-commit hooks installed"
fi

# Create .env from example
if [ ! -f ".env" ]; then
    echo ""
    read -p "📝 Create .env file from template? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✓ .env file created - please configure it"
    fi
fi

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Configure .env file if needed"
echo "   2. Run tests: pytest"
echo "   3. Start server: ./start.py or python main.py"
echo ""
echo "📚 Useful commands:"
echo "   - Run tests: pytest"
echo "   - Test coverage: pytest --cov=app --cov-report=html"
echo "   - Generate coverage badge: ./generate_coverage.py"
echo "   - Start server: ./start.py"
echo "   - Format code: ruff format src/ tests/"
echo "   - Lint code: ruff check src/ tests/"
echo ""
echo "🌐 Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo ""
echo "Happy coding! 🎉"

