# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Fixed pyproject.toml structure for proper dependency management
- Configured GitHub Actions permissions

### Added
- Initial project setup with FastAPI
- Multi-source market data scraping (Proimobil, Accesimobil, 999.md)
- Statistical analysis with quartiles and outlier detection
- Price distribution histograms
- Exchange rates from BNM (EUR/MDL, USD/MDL)
- PDF report generation with WeasyPrint
- Intelligent caching with 30-minute TTL
- Background scheduler for automatic data refresh
- Comprehensive test suite with >80% coverage
- Colored, structured logging
- CORS middleware support
- GitHub Actions CI/CD pipeline
- Comprehensive documentation

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A


### Security
- N/A

## [0.1.0] - 2025-11-20

### Added
- Initial release
- Core API functionality
- Web scraping for 3 major platforms
- Statistical analysis tools
- PDF generation service
- Caching and scheduling system

---

## Release Notes Format

### Version Types
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

### Change Categories
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

