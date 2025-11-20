# Services Layer

This directory contains business logic and orchestration services.

## Structure

- **cache.py** - Market data caching and background refresh scheduler
- **histogram.py** - Price distribution histogram calculation
- **proimobil_api_service.py** - Proimobil API data aggregation service
- **quartile_analysis.py** - Statistical quartile analysis
- **rates.py** - Exchange rates fetching service

## Responsibilities

- Business logic orchestration
- Aggregating data from multiple scrapers
- Complex calculations and transformations
- Caching strategies
- Background job scheduling

## Best Practices

- Services can call scrapers but not vice versa
- Services should not depend on FastAPI (use plain Python)
- Use dependency injection for settings
- Services should be testable without HTTP layer

