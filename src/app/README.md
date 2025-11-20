# App - Project Structure

## Overview

This project follows a clean architecture pattern with clear separation of concerns.

```
app/
├��─ core/           # Infrastructure (config, logging, deps)
├── api/            # FastAPI routes (HTTP layer)
├── services/       # Business logic orchestration
├── scraping/       # External data fetching (web scraping)
├── domain/         # Pure business logic & models
├── schemas/        # Pydantic models for API (future)
├── templates/      # HTML templates for PDF generation
└── static/         # Static assets (CSS, fonts)
```

## Layer Responsibilities

### 1. **Core** (`core/`)
- Application configuration (settings)
- Logging setup
- Dependency injection utilities
- **Dependencies:** None (foundation layer)

### 2. **Domain** (`domain/`)
- Pure business logic (calculations, transformations)
- Domain models (dataclasses, Pydantic models)
- Business rules
- **Dependencies:** None (can be used by all other layers)

### 3. **Scraping** (`scraping/`)
- Web scraping implementations
- External API integrations
- Data extraction from HTML/JSON
- **Dependencies:** `domain/` for models

### 4. **Services** (`services/`)
- Business logic orchestration
- Aggregating data from multiple sources
- Caching and background jobs
- Complex calculations
- **Dependencies:** `domain/`, `scraping/`, `core/`

### 5. **API** (`api/`)
- FastAPI route handlers
- Request/response models
- HTTP-specific logic
- **Dependencies:** `services/`, `domain/`, `core/`

## Dependency Rules

```
api/       → services/ → scraping/ → domain/
   ↓            ↓            ↓          ↑
core/ ←──────────────────────────────────┘
```

**Rules:**
- Lower layers cannot import from upper layers
- `domain/` has no dependencies (except stdlib)
- `core/` is used by all layers but doesn't depend on them
- Tests can import from any layer

## Best Practices

1. **Keep routers thin** - Business logic in `services/`
2. **Pure domain logic** - No I/O in `domain/`
3. **Independent scrapers** - Each scraper is self-contained
4. **Service orchestration** - Services combine multiple scrapers
5. **Configuration via environment** - Use `.env` + `core/config.py`

## Testing

Tests mirror the source structure:
```
tests/
├── test_calc.py              # domain/calc.py
├── test_market_stats.py      # domain/market_stats.py
├── test_proimobil.py         # scraping/proimobil.py
├── test_cache.py             # services/cache.py
└── test_market_router.py     # api/market_router.py
```

## Migration from Old Structure

Old → New mapping:
- `market_proimobil.py` → `scraping/proimobil.py`
- `market_accesimobil.py` → `scraping/accesimobil.py`
- `settings.py` → `core/config.py`
- `calc.py` → `domain/calc.py`
- `market_stats.py` → `domain/market_stats.py`
- `services/market/cache.py` → `services/cache.py`

