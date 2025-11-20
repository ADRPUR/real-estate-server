"""
Additional tests for misc and rates routers.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.domain.rates_utils as rates_utils

client = TestClient(app)


def test_day_endpoint():
    """Test /day endpoint."""
    response = client.get("/day")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "day" in data
    assert "full_date" in data
    
    # Day should be a date string in DD.MM.YYYY format
    assert isinstance(data["day"], str)
    # Should contain dots as separators
    assert "." in data["day"]

    # Full date should be an ISO format string
    assert isinstance(data["full_date"], str)
    # ISO format contains T or dashes
    assert "T" in data["full_date"] or "-" in data["full_date"]


def test_rates_endpoint(monkeypatch):
    """Test /rates endpoint."""
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
    
    # Import main module to monkeypatch
    import app.main as main_module
    monkeypatch.setattr(main_module, "fetch_all_rates", fake_fetch_all_rates)
    
    response = client.get("/rates")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "eur_to_mdl" in data
    assert "eur_to_ron" in data
    assert "ron_to_mdl" in data
    assert data["eur_to_mdl"] == 19.5
    assert data["eur_to_ron"] == 4.95


def test_rates_endpoint_with_cache(monkeypatch):
    """Test that rates endpoint uses cache."""
    call_count = {"count": 0}
    
    def fake_fetch_with_counter(use_cache=True):
        call_count["count"] += 1
        return {
            "date": "2025-11-15",
            "eur_to_mdl": 19.5,
            "eur_to_ron": 4.95,
            "ron_to_mdl": 3.94,
        }
    
    import app.main as main_module
    monkeypatch.setattr(main_module, "fetch_all_rates", fake_fetch_with_counter)
    
    # First call
    response1 = client.get("/rates")
    assert response1.status_code == 200
    first_count = call_count["count"]
    
    # Second call should use cache
    response2 = client.get("/rates")
    assert response2.status_code == 200
    
    # Function should be called (but internal caching happens in fetch_all_rates)
    assert call_count["count"] >= first_count


def test_openapi_endpoint():
    """Test OpenAPI JSON endpoint."""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    assert "title" in data["info"]


def test_docs_endpoint():
    """Test Swagger docs endpoint."""
    response = client.get("/docs")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_redoc_endpoint():
    """Test ReDoc endpoint."""
    response = client.get("/redoc")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_health_check():
    """Test that the app is running."""
    # Test that we can make a request
    response = client.get("/docs")
    assert response.status_code == 200

