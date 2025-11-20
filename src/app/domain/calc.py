from typing import Any, Dict
import logging
logger = logging.getLogger(__name__)


def _f(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def calculate(config: Dict[str, Any]) -> Dict[str, float]:
    logger.info("Starting calculation")
    new_apartment = config.get("new_apartment", {}) or {}
    old_apartment = config.get("old_apartment", {}) or {}
    exchange_rates = config.get("exchange_rates", {}) or {}
    currency_conversion = config.get("currency_conversion", {}) or {}
    notary_tax = config.get("notary_tax", {}) or {}
    agent_fee = config.get("agent_fee", {}) or {}
    income_tax = config.get("income_tax", {}) or {}
    rental_income = config.get("rental_income", {}) or {}

    include_parking = bool(new_apartment.get("include_parking_in_calculation", False))
    price_apartment = _f(new_apartment.get("price_apartment"))
    price_parking = _f(new_apartment.get("price_parking"))
    target_base = price_apartment + (price_parking if include_parking else 0)

    notary_enabled = bool(notary_tax.get("enabled", False))
    notary_pct = _f(notary_tax.get("percentage")) if notary_enabled else 0.0
    notary_tax_val = target_base * notary_pct / 100.0
    target_with_notary = target_base + notary_tax_val

    old_purchase = _f(old_apartment.get("purchase_price"))
    eur_to_mdl = _f(exchange_rates.get("eur_to_mdl"))
    eur_to_ron = _f(exchange_rates.get("eur_to_ron"))
    ron_to_mdl = _f(exchange_rates.get("ron_to_mdl"))

    s = _f(old_apartment.get("surface_area_sqm"))
    min_mp = avg_mp = max_mp = 0.0
    if s > 0:
        mp_avg = old_apartment.get("market_price_per_sqm_avg")
        mp_single = old_apartment.get("market_price_per_sqm")
        if mp_avg is not None:
            avg_mp = _f(mp_avg)
            min_mp = _f(old_apartment.get("market_price_per_sqm_min", 0))
            max_mp = _f(old_apartment.get("market_price_per_sqm_max", 0))
        elif mp_single is not None:
            avg_mp = _f(mp_single)
            min_mp = avg_mp * 0.9
            max_mp = avg_mp * 1.1
    market_min = s * min_mp
    market_avg = s * avg_mp
    market_max = s * max_mp

    agent_enabled = bool(agent_fee.get("enabled", False))
    agent_pct = _f(agent_fee.get("percentage"))
    agent_coef = agent_pct / 100.0 if agent_enabled else 0.0

    income_enabled = bool(income_tax.get("enabled", False))
    tax_rate = _f(income_tax.get("rate")) if income_enabled else 0.0
    tax_coef = tax_rate / 200.0 if income_enabled else 0.0

    if bool(rental_income.get("enabled", False)):
        monthly_amount = _f(rental_income.get("monthly_amount"))
        months_lost = _f(rental_income.get("months_lost"))
        lost_rental = monthly_amount * months_lost
    else:
        lost_rental = 0.0

    conversion_enabled = bool(currency_conversion.get("enabled", False))
    mdl_needed_for_ron = eur_to_ron * ron_to_mdl
    conversion_coef = ((mdl_needed_for_ron - eur_to_mdl) / eur_to_mdl) if (conversion_enabled and eur_to_mdl > 0) else 0.0

    denom = (1 - agent_coef - tax_coef) * (1 - conversion_coef)
    if denom <= 0:
        return {"error": 1, "message": "Coefficients (agent/tax/convert) produce denom=0; adjust percentages."}

    numerator = target_with_notary + lost_rental * (1 - conversion_coef)
    if income_enabled:
        numerator -= old_purchase * tax_coef * (1 - conversion_coef)

    sale_price = numerator / denom
    agent_fee_val = sale_price * agent_coef
    profit = sale_price - old_purchase
    tax_val = 0.0
    if income_enabled and profit > 0:
        tax_val = (profit / 2.0) * (tax_rate / 100.0)

    net_before_conv = sale_price - agent_fee_val - tax_val - lost_rental
    conv_cost = net_before_conv * conversion_coef if conversion_enabled else 0.0
    net = net_before_conv - conv_cost

    sale_mdl = sale_price * eur_to_mdl
    sale_ron = sale_price * eur_to_ron
    agent_mdl = agent_fee_val * eur_to_mdl
    tax_mdl = tax_val * eur_to_mdl
    lost_mdl = lost_rental * eur_to_mdl
    net_before_conv_mdl = net_before_conv * eur_to_mdl
    conv_cost_mdl = conv_cost * eur_to_mdl
    notary_tax_ron = notary_tax_val * eur_to_ron
    net_ron = net * eur_to_ron

    cover_pct = (net / target_with_notary * 100.0) if target_with_notary > 0 else 0.0
    inv_return_pct = ((profit / old_purchase) * 100.0) if old_purchase > 0 else 0.0

    return {
        "salePrice": sale_price,
        "saleMDL": sale_mdl,
        "saleRON": sale_ron,
        "targetWithNotary": target_with_notary,
        "notaryTax": notary_tax_val,
        "notaryTaxRON": notary_tax_ron,
        "marketMin": market_min,
        "marketAvg": market_avg,
        "marketMax": market_max,
        "minMp": min_mp,
        "avgMp": avg_mp,
        "maxMp": max_mp,
        "s": s,
        "agentFee": agent_fee_val,
        "agentMDL": agent_mdl,
        "profit": profit,
        "tax": tax_val,
        "taxMDL": tax_mdl,
        "lostRental": lost_rental,
        "lostMDL": lost_mdl,
        "conversionPct": conversion_coef * 100.0 if conversion_enabled else 0.0,
        "convCost": conv_cost,
        "convCostMDL": conv_cost_mdl,
        "eur_to_mdl": eur_to_mdl,
        "eur_to_ron": eur_to_ron,
        "ron_to_mdl": ron_to_mdl,
        "netBeforeConv": net_before_conv,
        "netBeforeConvMDL": net_before_conv_mdl,
        "netRON": net_ron,
        "net": net,
        "verificationDiff": abs(net - target_with_notary),
        "coverPct": cover_pct,
        "invReturnPct": inv_return_pct,
    }


def calculate_sale_summary(config: Dict[str, Any], amount: float, currency: str) -> Dict[str, float]:
    logger.info(f"Starting sale summary calculation - amount: {amount}, currency: {currency}")
    old_apartment = config.get("old_apartment", {}) or {}
    agent_fee_cfg = config.get("agent_fee", {}) or {}
    income_tax_cfg = config.get("income_tax", {}) or {}
    exchange_rates = config.get("exchange_rates", {}) or {}

    eur_to_mdl = _f(exchange_rates.get("eur_to_mdl"))
    if currency.upper() == "EUR":
        sale_eur = _f(amount)
    else:
        if eur_to_mdl <= 0:
            raise ValueError("eur_to_mdl must be > 0 for MDL sale price")
        sale_eur = _f(amount) / eur_to_mdl

    sale_mdl = sale_eur * eur_to_mdl
    purchase = _f(old_apartment.get("purchase_price"))

    agent_enabled = bool(agent_fee_cfg.get("enabled", False))
    agent_pct = _f(agent_fee_cfg.get("percentage"))
    agent_coef = agent_pct / 100.0 if agent_enabled else 0.0
    agent_fee_eur = sale_eur * agent_coef
    agent_fee_mdl = agent_fee_eur * eur_to_mdl

    gross_profit_eur = sale_eur - purchase
    gross_profit_mdl = gross_profit_eur * eur_to_mdl

    income_enabled = bool(income_tax_cfg.get("enabled", False))
    tax_rate = _f(income_tax_cfg.get("rate")) if income_enabled else 0.0

    if income_enabled and gross_profit_eur > 0:
        tax_eur = (gross_profit_eur / 2.0) * (tax_rate / 100.0)
    else:
        tax_eur = 0.0
    tax_mdl = tax_eur * eur_to_mdl

    net_profit_eur = gross_profit_eur - agent_fee_eur - tax_eur
    net_profit_mdl = net_profit_eur * eur_to_mdl

    net_income_eur = sale_eur - agent_fee_eur - tax_eur
    net_income_mdl = sale_mdl - agent_fee_mdl - tax_mdl

    return {
        "sale_eur": sale_eur,
        "sale_mdl": sale_mdl,
        "agent_fee_eur": agent_fee_eur,
        "agent_fee_mdl": agent_fee_mdl,
        "tax_eur": tax_eur,
        "tax_mdl": tax_mdl,
        "gross_profit_eur": gross_profit_eur,
        "gross_profit_mdl": gross_profit_mdl,
        "net_profit_eur": net_profit_eur,
        "net_profit_mdl": net_profit_mdl,
        "net_income_eur": net_income_eur,
        "net_income_mdl": net_income_mdl,
    }

__all__ = ["calculate", "calculate_sale_summary", "_f"]
