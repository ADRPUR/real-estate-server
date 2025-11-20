"""
Service layer for proimobil REST API (direct API calls, no scraping).
"""

import logging
from typing import Dict, Any, List
from app.scraping.proimobil_api import (
    fetch_all_proimobil_api_listings
)
from app.services.histogram import build_price_histogram
from app.services.quartile_analysis import calculate_quartiles
from app.domain.market_stats import MarketStats
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def compute_proimobil_api_stats(max_items: int = None) -> MarketStats:
    """
    Compute market statistics from proimobil.md REST API.

    Args:
        max_items: Maximum number of items to fetch (uses 500 if None)

    Returns:
        MarketStats object with computed statistics
    """
    if max_items is None:
        max_items = 500  # Default for API

    try:
        logger.info(f"Computing proimobil API stats (max_items={max_items})")

        # Fetch all listings
        listings = fetch_all_proimobil_api_listings(max_items)

        if not listings:
            logger.warning("No listings found from proimobil API")
            return MarketStats(
                source="proimobil_api",
                url="https://api.proimobil.md/v1/properties",
                total_ads=0,
                min_price_per_sqm=0.0,
                max_price_per_sqm=0.0,
                avg_price_per_sqm=0.0,
                median_price_per_sqm=0.0
            )

        # Extract prices per sqm
        prices = [listing.price_per_sqm for listing in listings if listing.price_per_sqm > 0]

        if not prices:
            logger.warning("No valid prices found from proimobil API listings")
            return MarketStats(
                source="proimobil_api",
                url="https://api.proimobil.md/v1/properties",
                total_ads=len(listings),
                min_price_per_sqm=0.0,
                max_price_per_sqm=0.0,
                avg_price_per_sqm=0.0,
                median_price_per_sqm=0.0
            )

        # Sort prices for statistics
        sorted_prices = sorted(prices)

        # Basic statistics
        min_price = sorted_prices[0]
        max_price = sorted_prices[-1]
        avg_price = sum(sorted_prices) / len(sorted_prices)

        # Median
        n = len(sorted_prices)
        if n % 2 == 0:
            median_price = (sorted_prices[n // 2 - 1] + sorted_prices[n // 2]) / 2
        else:
            median_price = sorted_prices[n // 2]

        # Compute histogram
        histogram = build_price_histogram(sorted_prices)

        # Find dominant range
        dominant_bin = max(histogram, key=lambda b: b.count) if histogram else None
        dominant_range = dominant_bin.label if dominant_bin else ""
        dominant_percentage = dominant_bin.percentage if dominant_bin else 0.0

        # Compute quartiles
        quartile_info = calculate_quartiles(sorted_prices)

        stats = MarketStats(
            source="proimobil_api",
            url="https://api.proimobil.md/v1/properties",
            total_ads=len(listings),
            min_price_per_sqm=round(min_price, 2),
            max_price_per_sqm=round(max_price, 2),
            avg_price_per_sqm=round(avg_price, 2),
            median_price_per_sqm=round(median_price, 2),
            price_histogram=histogram,
            dominant_range=dominant_range,
            dominant_percentage=round(dominant_percentage, 1),
            q1_price_per_sqm=round(quartile_info.get("q1", 0), 2),
            q2_price_per_sqm=round(quartile_info.get("q2", median_price), 2),
            q3_price_per_sqm=round(quartile_info.get("q3", 0), 2),
            iqr_price_per_sqm=round(quartile_info.get("iqr", 0), 2)
        )

        logger.info(f"Proimobil API stats: {len(listings)} ads, "
                   f"avg={avg_price:.2f} €/m², median={median_price:.2f} €/m²")

        return stats

    except Exception as e:
        logger.error(f"Error computing proimobil API stats: {e}", exc_info=True)
        return MarketStats(
            source="proimobil_api",
            url="https://api.proimobil.md/v1/properties",
            total_ads=0,
            min_price_per_sqm=0.0,
            max_price_per_sqm=0.0,
            avg_price_per_sqm=0.0,
            median_price_per_sqm=0.0
        )


def get_detailed_proimobil_api_listings(max_items: int = None) -> List[Dict[str, Any]]:
    """
    Get detailed listing information from proimobil REST API.

    Args:
        max_items: Maximum number of items to fetch

    Returns:
        List of dictionaries with detailed listing info
    """
    if max_items is None:
        max_items = 500

    listings = fetch_all_proimobil_api_listings(max_items)

    return [
        {
            "price_eur": listing.price_eur,
            "price_per_sqm": round(listing.price_per_sqm, 2),
            "city": listing.city,
            "sector": listing.sector,
            "street": listing.street,
            "rooms": listing.rooms,
            "surface_sqm": listing.surface_sqm,
            "url": f"https://proimobil.md/{listing.url_slug}" if listing.url_slug else None
        }
        for listing in listings
    ]

