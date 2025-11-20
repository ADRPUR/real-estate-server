"""
Calculation service - wrapper for domain calculation logic.

This service orchestrates calculation operations and integrates
with market data and rates services.
"""
import logging
from typing import Dict, Any, Optional

from app.domain.calc import calculate_sale_summary as domain_calculate
from app.services.rates import fetch_all_rates

logger = logging.getLogger(__name__)


def calculate_sale_summary(
    sale_price_eur: float,
    eur_to_mdl: Optional[float] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Calculate sale summary with all fees and conversions.

    Args:
        sale_price_eur: Sale price in EUR
        eur_to_mdl: EUR to MDL exchange rate (if None, will fetch)
        use_cache: Whether to use cached rates

    Returns:
        Dictionary with calculation results
    """
    logger.info(f"Calculating sale summary for EUR {sale_price_eur:,.2f}")

    # Fetch rates if not provided
    if eur_to_mdl is None:
        rates = fetch_all_rates(use_cache=use_cache)
        eur_to_mdl = rates.get("eur_to_mdl")

        if eur_to_mdl is None:
            logger.warning("Could not fetch EUR to MDL rate, using default")
            eur_to_mdl = 19.5  # fallback

    # Use domain calculation
    result = domain_calculate(sale_price_eur=sale_price_eur, eur_to_mdl=eur_to_mdl)

    logger.info(f"Sale summary calculated: total MDL {result.get('total_cost_mdl', 0):,.2f}")

    return result


def calculate_purchase_costs(
    price: float,
    currency: str = "EUR",
    surface: Optional[float] = None,
    parking_price: Optional[float] = None,
    parking_currency: Optional[str] = None,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Calculate all purchase costs including fees and taxes.

    Args:
        price: Purchase price
        currency: Price currency
        surface: Property surface in sqm
        parking_price: Parking price (optional)
        parking_currency: Parking currency (optional)
        use_cache: Whether to use cached rates

    Returns:
        Dictionary with all costs breakdown
    """
    logger.info(f"Calculating purchase costs for {currency} {price:,.2f}")

    # Fetch rates for conversions
    rates = fetch_all_rates(use_cache=use_cache)

    # Convert to EUR if needed
    price_eur = price
    if currency == "USD":
        usd_to_eur = 1.0 / rates.get("eur_to_usd", 1.1) if rates.get("eur_to_usd") else 0.91
        price_eur = price * usd_to_eur
    elif currency == "MDL":
        price_eur = price / rates.get("eur_to_mdl", 19.5)
    elif currency == "RON":
        price_eur = price / rates.get("eur_to_ron", 4.97)

    # Convert parking to EUR if provided
    parking_eur = 0
    if parking_price:
        parking_eur = parking_price
        if parking_currency == "USD":
            usd_to_eur = 1.0 / rates.get("eur_to_usd", 1.1) if rates.get("eur_to_usd") else 0.91
            parking_eur = parking_price * usd_to_eur
        elif parking_currency == "MDL":
            parking_eur = parking_price / rates.get("eur_to_mdl", 19.5)
        elif parking_currency == "RON":
            parking_eur = parking_price / rates.get("eur_to_ron", 4.97)

    total_price_eur = price_eur + parking_eur

    # Calculate using domain logic
    result = calculate_sale_summary(
        sale_price_eur=total_price_eur,
        eur_to_mdl=rates.get("eur_to_mdl"),
        use_cache=use_cache
    )

    # Add surface info if provided
    if surface:
        result["surface_sqm"] = surface
        result["price_per_sqm_eur"] = price_eur / surface
        result["price_per_sqm_mdl"] = result["price_per_sqm_eur"] * rates.get("eur_to_mdl", 19.5)

    return result

