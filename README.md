# 🏢 Real Estate Calculator API

[![CI/CD Pipeline](https://github.com/ADRPUR/real-estate-server/actions/workflows/ci.yml/badge.svg)](https://github.com/ADRPUR/real-estate-server/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ADRPUR/real-estate-server/branch/main/graph/badge.svg)](https://codecov.io/gh/ADRPUR/real-estate-server)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A comprehensive real estate market analysis API for Chisinau, Moldova. Aggregates and analyzes apartment listings from multiple sources (Proimobil, Accesimobil, 999.md) with advanced statistical analysis, PDF report generation, and real-time exchange rates.

## ✨ Features

- 📊 **Multi-Source Market Data**: Aggregates listings from 3 major real estate platforms
- 📈 **Statistical Analysis**: Quartile analysis, outlier detection, price distributions
- 💱 **Exchange Rates**: Real-time EUR/MDL and USD/MDL rates from BNM
- 📄 **PDF Reports**: Generate professional property evaluation reports
- 🚀 **High Performance**: Async operations with intelligent caching (30min TTL)
- 🔄 **Auto-Refresh**: Background scheduler for automatic data updates
- 🎨 **Beautiful Logs**: Colored, structured logging with timestamps
- 🌐 **CORS Support**: Ready for frontend integration
- 🧪 **Well Tested**: Comprehensive test suite with >80% coverage

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- System dependencies for WeasyPrint (PDF generation):

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libjpeg-dev libopenjp2-7-dev libffi-dev

# macOS
brew install pango cairo gdk-pixbuf libffi
```

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ADRPUR/real-estate-server.git
   cd real-estate-server
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   pip install -e ".[dev]"  # For development dependencies
   ```

4. **Install Playwright browsers** (for 999.md scraping)
   ```bash
   playwright install chromium
   ```

5. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## 🏃 Quick Start

### Using the start script (recommended)

```bash
./start.py
```

This will:
- ✅ Check and setup virtual environment
- ✅ Install package if needed
- ✅ Start the server on http://0.0.0.0:8000

### Manual start

```bash
python main.py
```

### Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📡 API Endpoints

### Market Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/market/summary` | GET | Aggregate market statistics from all sources |
| `/market/proimobil` | GET | Proimobil.md market data and statistics |
| `/market/accesimobil` | GET | Accesimobil.md market data and statistics |
| `/market/999md` | GET | 999.md market data (Playwright scraping) |
| `/market/proimobil/listings` | GET | All Proimobil listings with full details |

### Exchange Rates

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/rates` | GET | Current EUR/MDL and USD/MDL exchange rates from BNM |

### PDF Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/pdf/generate` | POST | Generate PDF evaluation report |

### Cache Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cache/refresh` | POST | Manually trigger cache refresh |
| `/cache/clear` | POST | Clear all cached data |
| `/cache/status` | GET | View cache status and metadata |

### Health Check

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | API health check |

## ⚙️ Configuration

Configuration is managed via environment variables with the `APP_` prefix or a `.env` file.

### Available Settings

```bash
# Market URLs (default: 2-room apartments, 40-60m², new construction)
APP_PROIMOBIL_URL="https://proimobil.md/..."
APP_ACCESIMOBIL_URL="https://accesimobil.md/..."
APP_MD999_URL="https://999.md/..."

# Cache Settings
APP_CACHE_TTL_MINUTES=30                  # Market data cache TTL
APP_SCRAPING_INTERVAL_MINUTES=30          # Auto-refresh interval
APP_MARKET_SUMMARY_TTL_MINUTES=15         # Summary endpoint cache
APP_FX_CACHE_TTL_SECONDS=1800             # Exchange rates cache (30min)

# Logging
APP_LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR

# CORS (JSON array)
APP_CORS_ORIGINS='["http://localhost:5173","https://your-frontend.com"]'
```

## 🛠️ Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Code Quality

```bash
# Linting with Ruff
ruff check src/ tests/

# Type checking with MyPy
mypy src/app --ignore-missing-imports

# Format code
ruff format src/ tests/
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py -v

# Run with markers
pytest -m "not slow"
```

### Generate Coverage Badge

```bash
coverage run -m pytest
coverage-badge -o coverage.svg -f
```

## 🧪 Testing

The project includes comprehensive tests covering:

- ✅ API endpoints (rates, market data, PDF generation)
- ✅ Scraping logic for all three sources
- ✅ Cache functionality
- ✅ Statistical calculations
- ✅ Error handling and edge cases

Current test coverage: **>80%**

Run tests with:
```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

## 📁 Project Structure

```
real-estate-server/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD
├── src/
│   └── app/
│       ├── api/
│       │   └── v1/             # API route handlers
│       │       ├── routes_market.py
│       │       ���── routes_rates.py
│       │       ├── routes_pdf.py
│       │       ├── routes_cache.py
│       │       └── routes_misc.py
│       ├── core/               # Configuration & settings
│       │   └─��� config.py
│       ├── domain/             # Business models
│       │   └── market_stats.py
│       ├── scraping/           # Web scraping logic
│       │   ├── proimobil.py
│       │   ├── proimobil_api.py
│       │   ├── accesimobil.py
│       │   └── md999.py
│       ├── services/           # Business logic
│       │   ├── cache.py
│       │   ├── histogram.py
│       │   ├── quartile_analysis.py
│       │   └── rates.py
│       ├── templates/          # Jinja2 templates for PDF
│       ├── static/             # Static assets
│       ���── main.py             # Application entry point
├── tests/                      # Test suite
│   ├── test_api.py
│   ├── test_calc.py
│   ├── test_scrapers.py
│   └── ...
├── main.py                     # CLI entry point
├── start.py                    # Smart startup script
├── pyproject.toml             # Project metadata & dependencies
├── requirements.txt           # Pip requirements
└── README.md                  # This file
```

## 🔄 How It Works

### Data Flow

```
┌─────────────────┐
│  External APIs  │
│  & Websites     │
└────────┬────────┘
         │
         ├─→ Proimobil.md (HTML scraping)
         ├─→ Accesimobil.md (HTML scraping)
         └─→ 999.md (Playwright dynamic scraping)
         │
         ↓
┌─────────────────┐
│  Scrapers       │  ← Extract listings & prices
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Services       │  ← Calculate stats, quartiles, distributions
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Cache Layer    │  ← 30min TTL, auto-refresh scheduler
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FastAPI        │  ← REST endpoints
└────────┬────────┘
         │
         ↓
   JSON Response
```

### Caching Strategy

- **Market Data**: Cached for 30 minutes, auto-refreshed by background scheduler
- **Exchange Rates**: Cached for 30 minutes (BNM updates daily)
- **Summary Endpoint**: Cached for 15 minutes (fast aggregation)
- **Manual Refresh**: Available via `/cache/refresh` endpoint

### Background Scheduler

The app uses APScheduler to automatically refresh market data:
- Starts on application startup
- Runs every 30 minutes (configurable)
- Logs cache updates with colorful, structured logs

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Write tests** for your changes
4. **Ensure tests pass** (`pytest`)
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your branch (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Code Standards

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for functions and classes
- Maintain test coverage above 80%
- Run `ruff` and `mypy` before committing

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@ADRPUR](https://github.com/ADRPUR)
- Email: apurice@gmail.com

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Playwright](https://playwright.dev/) - Dynamic content scraping
- [WeasyPrint](https://weasyprint.org/) - PDF generation
- [APScheduler](https://apscheduler.readthedocs.io/) - Background task scheduling

## 📊 Statistics

- **Lines of Code**: ~2,500+
- **Test Coverage**: >80%
- **API Endpoints**: 15+
- **Data Sources**: 3 major platforms
- **Python Version**: 3.11+

---

**Made with ❤️ for the Moldovan real estate market**

