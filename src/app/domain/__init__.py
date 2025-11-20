"""
Domain layer - pure business logic and domain models.

This layer contains the core business logic with no external dependencies.
All functions here should be deterministic and side-effect free.
"""
from app.domain.calc import calculate_sale_summary
from app.domain.finance import (
    calculate_notary_fee,
    calculate_registration_fee,
    calculate_real_estate_agency_fee,
    calculate_valuation_fee,
    calculate_total_purchase_costs,
    calculate_price_per_sqm,
    convert_currency,
)
from app.domain.market_stats import MarketStats
from app.domain.market_utils import build_price_histogram, get_price_distribution_summary
from app.domain.rates_utils import fetch_all_rates

__all__ = [
    # Calculations
    "calculate_sale_summary",
    # Finance
    "calculate_notary_fee",
    "calculate_registration_fee",
    "calculate_real_estate_agency_fee",
    "calculate_valuation_fee",
    "calculate_total_purchase_costs",
    "calculate_price_per_sqm",
    "convert_currency",
    # Market
    "MarketStats",
    "build_price_histogram",
    "get_price_distribution_summary",
    # Rates
    "fetch_all_rates",
]

