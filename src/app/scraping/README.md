# Scraping Layer

This directory contains all web scraping implementations for external data sources.

## Structure

- **proimobil.py** - HTML scraping for proimobil.md
- **proimobil_api.py** - Direct API integration for proimobil.md (faster, more reliable)
- **accesimobil.py** - HTML scraping for accesimobil.md
- **md999.py** - Selenium/Playwright scraping for 999.md (dynamic content)

## Responsibilities

- Fetching data from external websites
- Parsing HTML/JSON responses
- Extracting structured data (prices, addresses, etc.)
- Handling pagination
- Error handling for network issues

## Best Practices

- Each scraper should be independent and testable
- Use session objects for connection pooling
- Implement retry logic for transient failures
- Respect rate limits and add delays if needed
- Return domain models (not HTML/raw data)
- Handle SSL certificate issues gracefully

