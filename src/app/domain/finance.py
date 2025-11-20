"""
Pure financial calculation logic (domain layer).

This module contains pure business logic for financial calculations
with no external dependencies. All calculation functions are deterministic
and side-effect free.
"""
from typing import Dict, Any, Optional


def calculate_notary_fee(sale_price_mdl: float) -> float:
    """
    Calculate notary fee based on sale price in MDL.

    Fee structure:
    - 2% for amounts up to 300,000 MDL
    - 1% for amounts between 300,001 and 1,500,000 MDL
    - 0.5% for amounts over 1,500,000 MDL
    - Minimum fee: 1,000 MDL

    Args:
        sale_price_mdl: Sale price in MDL

    Returns:
        Notary fee in MDL
    """
    if sale_price_mdl <= 300_000:
        fee = sale_price_mdl * 0.02
    elif sale_price_mdl <= 1_500_000:
        fee = 300_000 * 0.02 + (sale_price_mdl - 300_000) * 0.01
    else:
        fee = 300_000 * 0.02 + 1_200_000 * 0.01 + (sale_price_mdl - 1_500_000) * 0.005

    return max(fee, 1_000)  # Minimum 1,000 MDL


def calculate_registration_fee(sale_price_mdl: float) -> float:
    """
    Calculate property registration fee (0.1% of sale price, min 1,000 MDL).

    Args:
        sale_price_mdl: Sale price in MDL

    Returns:
        Registration fee in MDL
    """
    fee = sale_price_mdl * 0.001
    return max(fee, 1_000)


def calculate_real_estate_agency_fee(sale_price_mdl: float, rate: float = 0.02) -> float:
    """
    Calculate real estate agency commission.

    Args:
        sale_price_mdl: Sale price in MDL
        rate: Commission rate (default 2%)

    Returns:
        Agency fee in MDL
    """
    return sale_price_mdl * rate


def calculate_valuation_fee(base_fee: float = 3_000) -> float:
    """
    Calculate property valuation fee.

    Args:
        base_fee: Base valuation fee in MDL (default 3,000)

    Returns:
        Valuation fee in MDL
    """
    return base_fee


def calculate_total_purchase_costs(
    sale_price_eur: float,
    eur_to_mdl: float,
    include_agency: bool = True,
    agency_rate: float = 0.02,
    include_valuation: bool = True,
    valuation_fee_mdl: float = 3_000
) -> Dict[str, Any]:
    """
    Calculate all costs associated with property purchase.

    Args:
        sale_price_eur: Sale price in EUR
        eur_to_mdl: EUR to MDL exchange rate
        include_agency: Whether to include agency fee
        agency_rate: Agency commission rate
        include_valuation: Whether to include valuation fee
        valuation_fee_mdl: Valuation fee in MDL

    Returns:
        Dictionary with detailed cost breakdown
    """
    # Convert to MDL
    sale_price_mdl = sale_price_eur * eur_to_mdl

    # Calculate individual fees
    notary_fee = calculate_notary_fee(sale_price_mdl)
    registration_fee = calculate_registration_fee(sale_price_mdl)

    # Optional fees
    agency_fee = calculate_real_estate_agency_fee(sale_price_mdl, agency_rate) if include_agency else 0
    valuation_fee = calculate_valuation_fee(valuation_fee_mdl) if include_valuation else 0

    # Calculate totals
    total_fees_mdl = notary_fee + registration_fee + agency_fee + valuation_fee
    total_cost_mdl = sale_price_mdl + total_fees_mdl
    total_cost_eur = total_cost_mdl / eur_to_mdl

    return {
        "sale_price_eur": sale_price_eur,
        "sale_price_mdl": sale_price_mdl,
        "eur_to_mdl_rate": eur_to_mdl,
        "fees": {
            "notary_mdl": notary_fee,
            "notary_eur": notary_fee / eur_to_mdl,
            "registration_mdl": registration_fee,
            "registration_eur": registration_fee / eur_to_mdl,
            "agency_mdl": agency_fee,
            "agency_eur": agency_fee / eur_to_mdl,
            "valuation_mdl": valuation_fee,
            "valuation_eur": valuation_fee / eur_to_mdl,
            "total_fees_mdl": total_fees_mdl,
            "total_fees_eur": total_fees_mdl / eur_to_mdl,
        },
        "total_cost_mdl": total_cost_mdl,
        "total_cost_eur": total_cost_eur,
        "fees_percentage": (total_fees_mdl / sale_price_mdl * 100) if sale_price_mdl > 0 else 0,
    }


def calculate_price_per_sqm(price: float, surface: float, currency: str = "EUR") -> Dict[str, float]:
    """
    Calculate price per square meter.

    Args:
        price: Total price
        surface: Surface area in square meters
        currency: Currency of the price

    Returns:
        Dictionary with price per sqm calculation
    """
    if surface <= 0:
        raise ValueError("Surface must be greater than 0")

    price_per_sqm = price / surface

    return {
        "total_price": price,
        "surface_sqm": surface,
        "price_per_sqm": price_per_sqm,
        "currency": currency,
    }


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: Dict[str, float]
) -> float:
    """
    Convert amount between currencies using provided rates.

    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        rates: Dictionary of exchange rates

    Returns:
        Converted amount
    """
    if from_currency == to_currency:
        return amount

    # Convert to EUR first (base currency)
    if from_currency == "EUR":
        amount_eur = amount
    elif from_currency == "USD":
        rate = 1.0 / rates.get("eur_to_usd", 1.1) if rates.get("eur_to_usd") else 0.91
        amount_eur = amount * rate
    elif from_currency == "MDL":
        amount_eur = amount / rates.get("eur_to_mdl", 19.5)
    elif from_currency == "RON":
        amount_eur = amount / rates.get("eur_to_ron", 4.97)
    else:
        raise ValueError(f"Unsupported source currency: {from_currency}")

    # Convert from EUR to target currency
    if to_currency == "EUR":
        return amount_eur
    elif to_currency == "USD":
        return amount_eur * rates.get("eur_to_usd", 1.1)
    elif to_currency == "MDL":
        return amount_eur * rates.get("eur_to_mdl", 19.5)
    elif to_currency == "RON":
        return amount_eur * rates.get("eur_to_ron", 4.97)
    else:
        raise ValueError(f"Unsupported target currency: {to_currency}")

