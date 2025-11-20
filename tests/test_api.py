
from fastapi.testclient import TestClient
import app.main as main_module
from app.main import app
from app.domain.market_stats import MarketStats
import app.domain.rates_utils as rates_utils

# Monkeypatch helpers

def fake_fetch_all_rates(use_cache=True):
    return {
        "date": "2025-11-15",
        "eur_to_mdl": 19.5,
        "eur_to_mdl_label": "BNM official EUR/MDL (XML, 15.11.2025)",
        "eur_to_ron": 4.95,
        "eur_to_ron_label": "BNR official EUR/RON (XML, 15.11.2025)",
        "ron_to_mdl": 3.94,
        "ron_to_mdl_label": "BNM medium MDL/RON (XLS, 15.11.2025)",
    }

async def fake_compute_aggregate_market_summary():
    sources = [
        MarketStats("proimobil.md", "http://example.com/pro", 10, 1200.0, 1500.0, 1350.0, 1325.0,
                    q1_price_per_sqm=1250.0, q2_price_per_sqm=1325.0, q3_price_per_sqm=1450.0, iqr_price_per_sqm=200.0),
        MarketStats("accesimobil.md", "http://example.com/acc", 8, 1100.0, 1450.0, 1300.0, 1290.0,
                    q1_price_per_sqm=1200.0, q2_price_per_sqm=1290.0, q3_price_per_sqm=1400.0, iqr_price_per_sqm=200.0),
        MarketStats("all", None, 18, 1100.0, 1500.0, 1325.0, 1310.0,
                    q1_price_per_sqm=1225.0, q2_price_per_sqm=1310.0, q3_price_per_sqm=1425.0, iqr_price_per_sqm=200.0),
    ]

    quartile_analysis = {
        "q1": 1225.0,
        "q2": 1310.0,
        "q3": 1425.0,
        "iqr": 200.0,
        "total_ads": 18,
        "outliers_removed": 2,
        "outliers_percentage": 11.11,
        "interpretation": {
            "market_width": "narrow",
            "price_range_description": "Most prices are between 1225 €/m² (Q1) and 1425 €/m² (Q3)",
            "iqr_description": "The central price distribution has a width of 200 €/m²",
            "budget_range": "< 1225 €/m²",
            "affordable_range": "1225 - 1310 €/m²",
            "mid_range": "1310 - 1425 €/m²",
            "premium_range": "> 1425 €/m²",
        },
        "sources_breakdown": {
            "proimobil": 10,
            "accesimobil": 8,
            "999md": 0
        }
    }

    return {
        "sources": sources,
        "quartile_analysis": quartile_analysis
    }

client = TestClient(app)

def test_day_endpoint():
    r = client.get("/day")
    assert r.status_code == 200
    data = r.json()
    assert "day" in data
    assert "full_date" in data


def test_rates_endpoint(monkeypatch):
    monkeypatch.setattr(main_module, "fetch_all_rates", fake_fetch_all_rates)
    r = client.get("/rates")
    assert r.status_code == 200
    data = r.json()
    assert data["eur_to_mdl"] == 19.5
    assert data["eur_to_ron"] == 4.95
    assert data["ron_to_mdl"] == 3.94


def test_market_summary_endpoint(monkeypatch):
    monkeypatch.setattr(main_module, "compute_aggregate_market_summary", fake_compute_aggregate_market_summary)
    main_module._market_summary_cache = None
    main_module._market_summary_cache_ts = None
    r = client.get("/market/summary")
    assert r.status_code == 200
    data = r.json()

    # Check structure
    assert "sources" in data
    assert "quartile_analysis" in data

    # Check sources
    assert len(data["sources"]) == 3
    sources = {d["source"] for d in data["sources"]}
    assert {"proimobil.md", "accesimobil.md", "all"} == sources

    # Check quartile_analysis
    qa = data["quartile_analysis"]
    assert "q1" in qa
    assert "q2" in qa
    assert "q3" in qa
    assert "iqr" in qa
    assert "interpretation" in qa
    assert qa["total_ads"] == 18


def test_rates_fallback_cross_rate(monkeypatch):
    # Force cache invalidation
    rates_utils._RATES_CACHE_TS = None
    rates_utils._RATES_CACHE.clear()

    def fake_eur_mdl(session=None):
        return 20.0, "BNM official EUR/MDL (XML, 15.11.2025)", __import__('datetime').date.today()
    def fake_eur_ron(session=None):
        return 5.0, "BNR official EUR/RON (XML, 15.11.2025)"
    def fake_ron_raise(*args, **kwargs):
        raise RuntimeError("XLS failure")
    monkeypatch.setattr(rates_utils, "fetch_eur_mdl_from_bnm", fake_eur_mdl)
    monkeypatch.setattr(rates_utils, "fetch_eur_ron_from_bnr", fake_eur_ron)
    monkeypatch.setattr(rates_utils, "fetch_ron_mdl_from_bnm_xls", fake_ron_raise)
    # Patch the reference inside main module to point to the updated rates_utils.fetch_all_rates
    monkeypatch.setattr(main_module, "fetch_all_rates", rates_utils.fetch_all_rates)

    r = client.get("/rates")
    assert r.status_code == 200
    data = r.json()
    # Fallback cross-rate should be eur_to_mdl / eur_to_ron = 20 / 5 = 4.0
    assert abs(data["ron_to_mdl"] - 4.0) < 1e-9
    # Accept label case-insensitively
    assert "cross-rate" in data["ron_to_mdl_label"].lower()
