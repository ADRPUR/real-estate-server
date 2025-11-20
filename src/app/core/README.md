# Core Infrastructure

This directory contains core infrastructure components:

- **config.py** - Application settings and configuration (Pydantic Settings)
- **deps.py** - FastAPI dependency injection utilities
- **logging.py** - Logging configuration

These modules provide the foundation for the entire application and should not depend on other application modules (api, services, scraping).

