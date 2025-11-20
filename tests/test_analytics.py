"""
Tests for market analytics endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client and clear cache."""
    client = TestClient(app)
    # Clear cache before analytics tests
    client.post("/cache/clear")
    return client


def test_market_insights_endpoint(client: TestClient):
    """Test market insights endpoint."""
    response = client.get("/market/analytics/insights")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check structure
    assert "total_listings" in data
    assert "average_price_eur" in data
    assert "median_price_eur" in data
    assert "sector_stats" in data
    assert "top_sectors_by_volume" in data
    assert "top_sectors_by_price" in data
    assert "room_distribution" in data
    assert "price_ranges" in data
    assert "underpriced_count" in data
    assert "overpriced_count" in data
    assert "premium_features" in data
    assert "best_value_sectors" in data
    
    # Check types
    assert isinstance(data["total_listings"], int)
    assert isinstance(data["average_price_eur"], (int, float))
    assert isinstance(data["sector_stats"], dict)
    assert isinstance(data["top_sectors_by_volume"], list)
    assert isinstance(data["room_distribution"], dict)


def test_predict_price_endpoint(client: TestClient):
    """Test price prediction endpoint."""
    response = client.get("/market/analytics/predict-price?surface=55&rooms=2")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check structure
    assert "predicted_price_eur" in data
    assert "predicted_price_per_sqm" in data
    assert "confidence_interval" in data
    assert "inputs" in data
    assert "market_comparison" in data
    
    # Check confidence interval structure
    assert "min" in data["confidence_interval"]
    assert "max" in data["confidence_interval"]
    assert "confidence" in data["confidence_interval"]
    
    # Check values are reasonable
    assert data["predicted_price_eur"] > 0
    assert data["predicted_price_per_sqm"] > 0
    assert data["confidence_interval"]["min"] < data["predicted_price_eur"]
    assert data["confidence_interval"]["max"] > data["predicted_price_eur"]


def test_predict_price_with_sector(client: TestClient):
    """Test price prediction with sector parameter."""
    response = client.get("/market/analytics/predict-price?surface=55&rooms=2&sector=Botanica")
    assert response.status_code == 200
    
    data = response.json()
    assert data["inputs"]["sector"] == "Botanica"


def test_predict_price_validation(client: TestClient):
    """Test validation for price prediction."""
    # Missing parameters
    response = client.get("/market/analytics/predict-price")
    assert response.status_code == 422
    
    # Invalid surface (negative)
    response = client.get("/market/analytics/predict-price?surface=-10&rooms=2")
    assert response.status_code == 422
    
    # Invalid rooms (too many)
    response = client.get("/market/analytics/predict-price?surface=55&rooms=100")
    assert response.status_code == 422


def test_best_deals_endpoint(client: TestClient):
    """Test best deals endpoint."""
    response = client.get("/market/analytics/best-deals")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check structure
    assert "best_deals" in data
    assert "total_analyzed" in data
    assert "criteria" in data
    
    # Check deals structure
    assert isinstance(data["best_deals"], list)
    if data["best_deals"]:
        deal = data["best_deals"][0]
        assert "listing" in deal
        assert "score" in deal
        
        # Check score structure
        score = deal["score"]
        assert "overall_score" in score
        assert "price_score" in score
        assert "location_score" in score
        assert "size_score" in score
        assert "value_assessment" in score
        
        # Scores should be 0-100
        assert 0 <= score["overall_score"] <= 100
        assert 0 <= score["price_score"] <= 100
        assert 0 <= score["location_score"] <= 100


def test_best_deals_with_limit(client: TestClient):
    """Test best deals with custom limit."""
    response = client.get("/market/analytics/best-deals?limit=5")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["best_deals"]) <= 5


def test_property_score_endpoint(client: TestClient):
    """Test property score endpoint."""
    # First get a listing ID
    listings_response = client.get("/market/proimobil-api/listings")
    assert listings_response.status_code == 200
    
    listings_data = listings_response.json()
    if not listings_data["listings"]:
        pytest.skip("No listings available for testing")

    # Use ID first, fallback to url_slug
    listing = listings_data["listings"][0]
    listing_id = listing.get("id") or listing.get("url_slug")

    if not listing_id:
        pytest.skip("No valid ID found in listing")

    # Get score for this listing
    response = client.get(f"/market/analytics/property-score/{listing_id}")
    assert response.status_code == 200

    data = response.json()

    # Check structure
    assert "overall_score" in data
    assert "price_score" in data
    assert "location_score" in data
    assert "size_score" in data
    assert "value_assessment" in data
    assert "predicted_price_range" in data
    assert "vs_market_percentage" in data
    assert "listing_details" in data

    # Check value assessment is valid
    assert data["value_assessment"] in ["excellent", "good", "fair", "poor"]

    # Check scores are in range
    assert 0 <= data["overall_score"] <= 100


def test_property_score_not_found(client: TestClient):
    """Test property score with invalid ID."""
    response = client.get("/market/analytics/property-score/nonexistent-id-12345")
    assert response.status_code == 404


def test_similar_properties_endpoint(client: TestClient):
    """Test similar properties endpoint."""
    # First get a listing ID
    listings_response = client.get("/market/proimobil-api/listings")
    assert listings_response.status_code == 200
    
    listings_data = listings_response.json()
    if not listings_data["listings"]:
        pytest.skip("No listings available for testing")

    # Use ID first, fallback to url_slug
    listing = listings_data["listings"][0]
    listing_id = listing.get("id") or listing.get("url_slug")

    if not listing_id:
        pytest.skip("No valid ID found in listing")

    # Find similar properties
    response = client.get(f"/market/analytics/similar/{listing_id}")
    assert response.status_code == 200

        data = response.json()
        
        # Check structure
        assert "reference_property" in data
        assert "similar_properties" in data
        assert "total_found" in data
        
        # Check reference property
        ref = data["reference_property"]
        assert "id" in ref
        assert "price_eur" in ref
        assert "price_per_sqm" in ref
        
        # Check similar properties have similarity scores
        if data["similar_properties"]:
            similar = data["similar_properties"][0]
            assert "similarity_score" in similar
            assert 0 <= similar["similarity_score"] <= 100


def test_similar_properties_with_limit(client: TestClient):
    """Test similar properties with custom limit."""
    listings_response = client.get("/market/proimobil-api/listings")
    listings_data = listings_response.json()
    
    if not listings_data["listings"]:
        pytest.skip("No listings available for testing")

    # Use ID first, fallback to url_slug
    listing = listings_data["listings"][0]
    listing_id = listing.get("id") or listing.get("url_slug")

    if not listing_id:
        pytest.skip("No valid ID found in listing")

    response = client.get(f"/market/analytics/similar/{listing_id}?limit=3")
    assert response.status_code == 200

    data = response.json()
    assert len(data["similar_properties"]) <= 3


def test_similar_properties_not_found(client: TestClient):
    """Test similar properties with invalid ID."""
    response = client.get("/market/analytics/similar/nonexistent-id-12345")
    assert response.status_code == 404


def test_analytics_caching(client: TestClient):
    """Test that analytics endpoints use caching."""
    # First request
    response1 = client.get("/market/analytics/insights")
    assert response1.status_code == 200
    
    # Second request should be faster (cached)
    response2 = client.get("/market/analytics/insights")
    assert response2.status_code == 200
    
    # Data should be identical except for cache_info age_seconds
    data1 = response1.json()
    data2 = response2.json()

    # Remove cache_info before comparison (age_seconds will differ)
    data1_no_cache = {k: v for k, v in data1.items() if k != 'cache_info'}
    data2_no_cache = {k: v for k, v in data2.items() if k != 'cache_info'}

    assert data1_no_cache == data2_no_cache

    # But both should have cache_info
    if 'cache_info' in data1:
        assert 'cache_info' in data2


def test_sector_stats_structure(client: TestClient):
    """Test sector stats have correct structure."""
    response = client.get("/market/analytics/insights")
    assert response.status_code == 200
    
    data = response.json()
    sector_stats = data["sector_stats"]
    
    if sector_stats:
        # Pick first sector
        sector_name = list(sector_stats.keys())[0]
        sector_data = sector_stats[sector_name]
        
        # Check structure
        assert "count" in sector_data
        assert "avg_price_eur" in sector_data
        assert "avg_surface_sqm" in sector_data
        assert "avg_price_per_sqm" in sector_data
        assert "min_price" in sector_data
        assert "max_price" in sector_data
        
        # Check values are reasonable
        assert sector_data["count"] > 0
        assert sector_data["avg_price_eur"] > 0
        assert sector_data["min_price"] <= sector_data["max_price"]

