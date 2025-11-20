import sys, os
from app.domain.calc import calculate, calculate_sale_summary, _f

def test_helper_f_with_none():
    assert _f(None) == 0.0
    assert _f(None, 10.0) == 10.0

def test_helper_f_with_empty_string():
    assert _f("") == 0.0
    assert _f("", 5.0) == 5.0

def test_helper_f_with_valid():
    assert _f(123.45) == 123.45
    assert _f("678.9") == 678.9

def test_calculate_without_parking():
    config = {
        "new_apartment": {"price_apartment": 50000, "include_parking_in_calculation": False, "price_parking": 5000},
        "old_apartment": {"purchase_price": 40000},
        "exchange_rates": {"eur_to_mdl": 19.5, "eur_to_ron": 4.95, "ron_to_mdl": 3.94},
    }
    result = calculate(config)
    assert result["salePrice"] > 0
    assert result["targetWithNotary"] == 50000.0

def test_calculate_with_all_options_enabled():
    config = {
        "new_apartment": {"price_apartment": 80000, "price_parking": 8000, "include_parking_in_calculation": True},
        "old_apartment": {"purchase_price": 55000, "surface_area_sqm": 50, "market_price_per_sqm_avg": 1400, "market_price_per_sqm_min": 1300, "market_price_per_sqm_max": 1500},
        "exchange_rates": {"eur_to_mdl": 19.5, "eur_to_ron": 4.95, "ron_to_mdl": 3.94},
        "notary_tax": {"enabled": True, "percentage": 0.5},
        "agent_fee": {"enabled": True, "percentage": 2},
        "income_tax": {"enabled": True, "rate": 12},
        "rental_income": {"enabled": True, "monthly_amount": 500, "months_lost": 2},
        "currency_conversion": {"enabled": True},
    }
    result = calculate(config)
    assert result["salePrice"] > 0
    assert result["notaryTax"] > 0
    assert result["agentFee"] > 0
    assert result["tax"] >= 0
    assert result["lostRental"] > 0
    assert result["convCost"] >= 0
    assert result["marketMin"] == 50 * 1300
    assert result["marketAvg"] == 50 * 1400
    assert result["marketMax"] == 50 * 1500

def test_calculate_with_market_price_single():
    config = {
        "new_apartment": {"price_apartment": 50000},
        "old_apartment": {"purchase_price": 40000, "surface_area_sqm": 50, "market_price_per_sqm": 1400},
        "exchange_rates": {"eur_to_mdl": 19.5, "eur_to_ron": 4.95, "ron_to_mdl": 3.94},
    }
    result = calculate(config)
    assert result["avgMp"] == 1400
    assert result["minMp"] == 1400 * 0.9
    assert result["maxMp"] == 1400 * 1.1
