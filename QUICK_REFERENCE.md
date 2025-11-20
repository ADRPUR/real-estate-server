# Quick Reference Guide

## 🚀 Essential Commands

### Setup & Installation

```bash
# Quick setup (recommended)
./setup_dev.sh

# Manual setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

### Running the Server

```bash
# Using start script (auto-checks environment)
./start.py

# Direct run
python main.py

# With custom port
python -c "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8080)"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Run tests matching pattern
pytest -k "test_rates"

# Run fast tests only (skip slow scrapers)
pytest -m "not slow"

# Generate coverage badge
./generate_coverage.py
```

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Check linting
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/

# Type checking
mypy src/app --ignore-missing-imports

# Security scan
bandit -r src/ -f json -o bandit-report.json
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Commit with conventional commits
git commit -m "feat: add new feature"
git commit -m "fix: correct bug in calculation"
git commit -m "docs: update README"

# Push and create PR
git push origin feature/my-feature
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## 📊 Coverage Commands

```bash
# Generate HTML coverage report
coverage run -m pytest
coverage html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Generate badge
coverage-badge -o coverage.svg -f

# Check coverage threshold
coverage report --fail-under=80
```

## 🔍 Debugging

```bash
# Run tests with verbose output
pytest -vv

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run last failed tests only
pytest --lf

# Show slowest tests
pytest --durations=10
```

## 📦 Package Management

```bash
# Build package
python -m build

# Install locally
pip install -e .

# Update dependencies
pip install --upgrade -r requirements.txt

# Check outdated packages
pip list --outdated
```

## 🌐 API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get exchange rates
curl http://localhost:8000/rates

# Get market summary
curl http://localhost:8000/market/summary

# View API docs
open http://localhost:8000/docs  # macOS
xdg-open http://localhost:8000/docs  # Linux
```

## 🔄 Cache Management

```bash
# Check cache status
curl http://localhost:8000/cache/status

# Refresh cache manually
curl -X POST http://localhost:8000/cache/refresh

# Clear all cache
curl -X POST http://localhost:8000/cache/clear
```

## 📝 Documentation

```bash
# Generate API documentation (OpenAPI spec)
curl http://localhost:8000/openapi.json > openapi.json

# View ReDoc
open http://localhost:8000/redoc
```

## 🐳 Docker (Future)

```bash
# Build image
docker build -t real-estate-api .

# Run container
docker run -p 8000:8000 real-estate-api

# Run with .env
docker run --env-file .env -p 8000:8000 real-estate-api
```

## 🔧 Environment Variables

```bash
# Set log level
export APP_LOG_LEVEL=DEBUG

# Set cache TTL
export APP_CACHE_TTL_MINUTES=60

# Run with custom config
APP_LOG_LEVEL=DEBUG python main.py
```

## 📈 Performance

```bash
# Profile code
python -m cProfile -o profile.stats main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('time').print_stats(10)"

# Memory profiling
pip install memory_profiler
python -m memory_profiler main.py
```

## 🛠️ Maintenance

```bash
# Clean cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clean test artifacts
rm -rf .pytest_cache htmlcov .coverage

# Clean build artifacts
rm -rf build/ dist/ *.egg-info/

# Full clean
git clean -fdx -e .env -e .venv
```

## 📋 Useful One-Liners

```bash
# Count lines of code
find src -name "*.py" -exec wc -l {} + | tail -1

# Find TODOs
grep -rn "TODO" src/

# Check test coverage per file
pytest --cov=app --cov-report=term-missing | grep "src/app"

# Run tests in parallel
pytest -n auto

# Generate test report
pytest --html=report.html --self-contained-html
```

## 🎯 Git Aliases (Add to ~/.gitconfig)

```ini
[alias]
    # Shortcuts
    st = status
    co = checkout
    br = branch
    ci = commit
    
    # Useful commands
    lg = log --oneline --graph --decorate --all
    unstage = reset HEAD --
    last = log -1 HEAD
    
    # Conventional commits
    feat = "!f() { git commit -m \"feat: $*\"; }; f"
    fix = "!f() { git commit -m \"fix: $*\"; }; f"
    docs = "!f() { git commit -m \"docs: $*\"; }; f"
```

---

💡 **Pro Tip**: Add commonly used commands to shell aliases in `~/.bashrc` or `~/.zshrc`:

```bash
alias server='cd /path/to/project && ./start.py'
alias rtest='pytest --cov=app --cov-report=term-missing'
alias rfmt='ruff format src/ tests/'
```

