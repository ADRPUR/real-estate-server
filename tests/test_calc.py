from app.domain.calc import calculate, calculate_sale_summary

sample_config = {
    "new_apartment": {
        "price_apartment": 80000,
        "price_parking": 8000,
        "include_parking_in_calculation": True,
    },
    "old_apartment": {
        "purchase_price": 55000,
        "surface_area_sqm": 50,
        "market_price_per_sqm": 1400,
    },
    "exchange_rates": {
        "eur_to_mdl": 19.5,
        "eur_to_ron": 4.95,
        "ron_to_mdl": 3.94,
    },
    "notary_tax": {"enabled": True, "percentage": 0.5},
    "agent_fee": {"enabled": True, "percentage": 2},
    "income_tax": {"enabled": True, "rate": 12},
    "rental_income": {"enabled": True, "monthly_amount": 500, "months_lost": 2},
    "currency_conversion": {"enabled": True},
}

def test_calculate_basic():
    result = calculate(sample_config)
    assert "salePrice" in result
    assert result["salePrice"] > 0
    assert result["net"] < result["salePrice"]
    assert 0 <= result["coverPct"] <= 200

def test_sale_summary():
    sale = calculate_sale_summary(sample_config, amount=100000, currency="EUR")
    assert sale["sale_eur"] == 100000
    assert sale["sale_mdl"] == sale["sale_eur"] * sample_config["exchange_rates"]["eur_to_mdl"]
    assert sale["net_income_eur"] <= sale["sale_eur"]

def test_sale_summary_mdl_conversion():
    amount_mdl = 195000  # should become 10_000 EUR at eur_to_mdl=19.5
    sale = calculate_sale_summary(sample_config, amount=amount_mdl, currency="MDL")
    assert abs(sale["sale_eur"] - (amount_mdl / sample_config["exchange_rates"]["eur_to_mdl"])) < 1e-6
    # Ensure MDL round-trip
    assert abs(sale["sale_mdl"] - amount_mdl) < 1e-6
    # Net income cannot exceed sale amount in EUR
    assert sale["net_income_eur"] <= sale["sale_eur"]

def test_invalid_denominator():
    bad_config = {
        "new_apartment": {"price_apartment": 10000},
        "old_apartment": {"purchase_price": 5000},
        "exchange_rates": {"eur_to_mdl": 10, "eur_to_ron": 2, "ron_to_mdl": 20},  # conversion_coef = (40-10)/10 = 3.0 >1
        "agent_fee": {"enabled": True, "percentage": 50},  # large
        "income_tax": {"enabled": True, "rate": 50},
        "currency_conversion": {"enabled": True},
    }
    result = calculate(bad_config)
    assert result.get("error") == 1
    assert "denom" in result.get("message", "") or "Coefficients" in result.get("message", "")

def test_sale_summary_missing_eur_to_mdl():
    cfg = {
        "old_apartment": {"purchase_price": 10000},
        "exchange_rates": {"eur_to_mdl": 0},
        "agent_fee": {"enabled": False},
        "income_tax": {"enabled": False},
    }
    try:
        calculate_sale_summary(cfg, amount=100000, currency="MDL")
        assert False, "Expected ValueError for missing eur_to_mdl"
    except ValueError:
        pass
