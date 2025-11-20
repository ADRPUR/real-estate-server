# Contributing to Real Estate Calculator API

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/ADRPUR/real-estate-server.git
cd real-estate-server
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"

# Install Playwright
playwright install chromium
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-description
```

## 🔄 Development Workflow

### 1. Make Your Changes

- Write clean, readable code
- Follow the coding standards below
- Add tests for new functionality
- Update documentation as needed

### 2. Run Tests Locally

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific tests
pytest tests/test_api.py -v
```

### 3. Check Code Quality

```bash
# Linting
ruff check src/ tests/

# Type checking
mypy src/app --ignore-missing-imports

# Format code
ruff format src/ tests/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

See [Commit Messages](#commit-messages) for format guidelines.

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a Pull Request on GitHub.

## 📝 Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 100 characters (flexible for readability)
- Use type hints for function parameters and return values

### Example

```python
from typing import List, Optional

def calculate_average_price(
    prices: List[float],
    exclude_outliers: bool = True
) -> Optional[float]:
    """
    Calculate the average price per square meter.
    
    Args:
        prices: List of prices per square meter
        exclude_outliers: Whether to exclude statistical outliers
        
    Returns:
        Average price or None if list is empty
    """
    if not prices:
        return None
        
    # Implementation here
    return sum(prices) / len(prices)
```

### Code Organization

- Keep functions small and focused (single responsibility)
- Use descriptive variable and function names
- Add docstrings to all public functions and classes
- Group related functionality into modules
- Separate business logic from API layer

### Import Order

```python
# 1. Standard library
import os
from pathlib import Path
from datetime import datetime

# 2. Third-party packages
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

# 3. Local application imports
from app.core.config import get_settings
from app.services.cache import get_cache
```

## 🧪 Testing Guidelines

### Test Coverage

- Maintain test coverage above **80%**
- Write tests for all new features
- Include edge cases and error scenarios
- Use descriptive test names

### Test Structure

```python
def test_calculate_average_price_with_valid_data():
    """Test average calculation with valid price data."""
    # Arrange
    prices = [1500.0, 2000.0, 2500.0]
    
    # Act
    result = calculate_average_price(prices)
    
    # Assert
    assert result == 2000.0
    
def test_calculate_average_price_with_empty_list():
    """Test that empty list returns None."""
    result = calculate_average_price([])
    assert result is None
```

### Testing Best Practices

- ✅ Test public APIs, not implementation details
- ✅ Use fixtures for common test data
- ✅ Mock external dependencies (HTTP calls, file I/O)
- ✅ Test both success and failure scenarios
- ✅ Keep tests independent and isolated

### Running Specific Test Categories

```bash
# Run fast tests only
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run with verbose output
pytest -v --tb=short
```

## 💬 Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons, etc.)
- `refactor`: Code refactoring without changing functionality
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Build process, dependencies, tooling
- `ci`: CI/CD configuration changes

### Examples

```bash
# Feature
feat(scraping): add support for 999.md dynamic content

# Bug fix
fix(api): correct price calculation for edge case

# Documentation
docs(readme): update installation instructions

# Refactoring
refactor(cache): simplify cache invalidation logic

# Tests
test(api): add tests for market summary endpoint
```

### Guidelines

- Use imperative mood ("add feature" not "added feature")
- Don't capitalize first letter
- No period at the end
- Keep subject line under 50 characters
- Wrap body at 72 characters
- Reference issues in footer: `Fixes #123` or `Closes #456`

## 🔀 Pull Request Process

### Before Submitting

- ✅ All tests pass locally
- ✅ Code is formatted with Ruff
- ✅ No linting errors
- ✅ Documentation is updated
- ✅ Test coverage is maintained or improved
- ✅ Commit messages follow conventions

### PR Description Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Related Issues
Fixes #(issue number)
```

### Review Process

1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one maintainer approval required
3. **Testing**: Manual testing if needed
4. **Merge**: Squash and merge (maintainer will handle this)

### After Merge

- Delete your feature branch
- Update your fork's main branch
- Close related issues if not auto-closed

## 📁 Project Structure

Understanding the project structure helps you contribute effectively:

```
src/app/
├── api/v1/          # API route handlers
├── core/            # Configuration and settings
├── domain/          # Domain models (MarketStats, etc.)
├── scraping/        # Web scraping logic for each source
├── services/        # Business logic services
├── templates/       # Jinja2 templates for PDFs
└── main.py          # Application entry point

tests/
├── test_api.py      # API endpoint tests
├── test_calc.py     # Calculation logic tests
├── test_scrapers.py # Web scraping tests
└── conftest.py      # Pytest fixtures
```

## 🆘 Getting Help

- 💬 Open a [Discussion](https://github.com/ADRPUR/real-estate-server/discussions)
- 🐛 Report bugs via [Issues](https://github.com/ADRPUR/real-estate-server/issues)
- 📧 Contact maintainers: apurice@gmail.com

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Ruff Linter](https://github.com/astral-sh/ruff)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

Thank you for contributing! 🎉

