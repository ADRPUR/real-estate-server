"""
Rates service - wrapper for exchange rate fetching.

This service provides a clean interface for fetching and caching
exchange rates from various sources.
"""
import logging
from typing import Dict, Optional

from app.domain.rates_utils import fetch_all_rates as domain_fetch_rates

logger = logging.getLogger(__name__)

# Re-export the domain function for backward compatibility
# The actual implementation is in app.domain.rates_utils
fetch_all_rates = domain_fetch_rates

__all__ = ["fetch_all_rates"]

