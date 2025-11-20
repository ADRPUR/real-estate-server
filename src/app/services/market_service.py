"""
Market service - aggregation and orchestration of market data.

This service combines data from multiple scraping sources
(Proimobil, Accesimobil, 999.md) to provide unified market insights.
"""
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

from app.domain.market_stats import MarketStats
from app.scraping.proimobil import compute_proimobil_stats, fetch_all_proimobil_prices
from app.scraping.accesimobil import compute_stats_for_accesimobil, fetch_all_prices_accesimobil
from app.scraping.md999 import compute_999md_stats, fetch_all_999md_prices
from app.services.cache import get_market_cache

logger = logging.getLogger(__name__)


def get_market_data_aggregated(use_cache: bool = True) -> Dict[str, Any]:
    """
    Fetch and aggregate market data from all sources.

    Args:
        use_cache: Whether to use cached data

    Returns:
        Dictionary with aggregated market statistics
    """
    logger.info("Fetching aggregated market data from all sources")

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "sources": {}
    }

    # Try to get data from each source
    sources = [
        ("proimobil", compute_proimobil_stats),
        ("accesimobil", compute_stats_for_accesimobil),
        ("999md", compute_999md_stats)
    ]

    all_prices = []

    for source_name, fetch_func in sources:
        try:
            logger.info(f"Fetching {source_name} data...")

            # Check cache first
            cache = get_market_cache()
            cache_key = f"market_{source_name}"
            if use_cache:
                cached = cache.get(cache_key)
                if cached:
                    logger.info(f"Using cached {source_name} data")
                    result["sources"][source_name] = cached
                    if cached.get("prices"):
                        all_prices.extend(cached["prices"])
                    continue

            # Fetch fresh data
            stats = fetch_func()
            if stats:
                stats_dict = stats.to_dict() if hasattr(stats, "to_dict") else stats
                result["sources"][source_name] = stats_dict

                # Cache the result
                if use_cache:
                    cache.set(cache_key, stats_dict, source=source_name)

                # Collect prices for aggregation
                if isinstance(stats, MarketStats) and stats.prices:
                    all_prices.extend(stats.prices)

        except Exception as e:
            logger.error(f"Error fetching {source_name} data: {e}")
            result["sources"][source_name] = {"error": str(e)}

    # Calculate aggregate statistics if we have data
    if all_prices:
        from statistics import mean, median, stdev

        result["aggregate"] = {
            "total_listings": len(all_prices),
            "avg_price_per_sqm": mean(all_prices),
            "median_price_per_sqm": median(all_prices),
            "min_price_per_sqm": min(all_prices),
            "max_price_per_sqm": max(all_prices),
            "std_dev": stdev(all_prices) if len(all_prices) > 1 else 0,
            "currency": "EUR"
        }

        logger.info(f"Aggregated {len(all_prices)} total listings")

    return result


def get_proimobil_stats(use_cache: bool = True) -> Optional[MarketStats]:
    """
    Get Proimobil market statistics.

    Args:
        use_cache: Whether to use cached data

    Returns:
        MarketStats object or None
    """
    cache = get_market_cache()
    cache_key = "market_proimobil"

    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Using cached Proimobil data")
            return MarketStats(**cached) if isinstance(cached, dict) else cached

    logger.info("Fetching fresh Proimobil data")
    stats = compute_proimobil_stats()

    if stats and use_cache:
        cache.set(cache_key, stats.to_dict() if hasattr(stats, "to_dict") else stats, source="proimobil")

    return stats


def get_accesimobil_stats(use_cache: bool = True) -> Optional[MarketStats]:
    """
    Get Accesimobil market statistics.

    Args:
        use_cache: Whether to use cached data

    Returns:
        MarketStats object or None
    """
    cache = get_market_cache()
    cache_key = "market_accesimobil"

    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Using cached Accesimobil data")
            return MarketStats(**cached) if isinstance(cached, dict) else cached

    logger.info("Fetching fresh Accesimobil data")
    stats = compute_stats_for_accesimobil()

    if stats and use_cache:
        cache.set(cache_key, stats.to_dict() if hasattr(stats, "to_dict") else stats, source="accesimobil")

    return stats


def get_999md_stats(use_cache: bool = True) -> Optional[MarketStats]:
    """
    Get 999.md market statistics.

    Args:
        use_cache: Whether to use cached data

    Returns:
        MarketStats object or None
    """
    cache = get_market_cache()
    cache_key = "market_999md"

    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Using cached 999.md data")
            return MarketStats(**cached) if isinstance(cached, dict) else cached

    logger.info("Fetching fresh 999.md data")
    stats = compute_999md_stats()

    if stats and use_cache:
        cache.set(cache_key, stats.to_dict() if hasattr(stats, "to_dict") else stats, source="999md")

    return stats

