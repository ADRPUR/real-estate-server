# Domain Layer

This directory contains pure business logic and domain models.

## Structure

- **calc.py** - Financial calculations (mortgage, ROI, etc.)
- **market_stats.py** - Market statistics data models (MarketStats, HistogramBin, etc.)
- **market_utils.py** - Market data utilities and histogram builders
- **rates_utils.py** - Exchange rate utilities and fetching logic

## Responsibilities

- Pure business logic (no I/O, no side effects)
- Domain models (dataclasses, Pydantic models)
- Business rules and calculations
- Data transformations

## Best Practices

- No dependencies on FastAPI, databases, or external services
- Functions should be pure and testable
- Use dataclasses or Pydantic models for data structures
- Should not import from `api/`, `services/`, or `scraping/`
- Can be imported by any other layer

