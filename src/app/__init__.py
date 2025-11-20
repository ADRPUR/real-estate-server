"""Apartment Backend package.

Provides calculation logic, market scraping, FX rates fetching, and PDF generation.
"""
from importlib.metadata import version, PackageNotFoundError

__all__ = [
    # Core public modules
    "main",
    "settings",
    # Service namespaces
    "services",
    # Data models
    "market_stats",
]

try:  # safe version retrieval
    __version__ = version("apartment-backend")
except PackageNotFoundError:  # during editable install before metadata
    __version__ = "0.0.0-dev"
