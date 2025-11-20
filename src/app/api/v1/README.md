# API Layer

This directory contains all FastAPI route handlers (endpoints).

## Structure

- **cache_router.py** - Cache management endpoints
- **market_router.py** - Market data endpoints (proimobil, accesimobil, 999.md)
- **pdf_router.py** - PDF generation endpoints
- **rates_router.py** - Exchange rates endpoints
- **misc_router.py** - Miscellaneous endpoints (health check, etc.)

## Responsibilities

- HTTP request/response handling
- Request validation (Pydantic models)
- Response serialization
- Calling service layer for business logic
- NO business logic should be in routers - delegate to services/

## Best Practices

- Keep routers thin - business logic belongs in `services/`
- Use dependency injection for settings, DB sessions, etc.
- Return Pydantic models or dicts, not custom classes
- Handle exceptions and return appropriate HTTP status codes

