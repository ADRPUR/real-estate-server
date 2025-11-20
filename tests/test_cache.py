"""
Tests for cache functionality and cache router endpoints.
"""

from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.services.cache import (
    MarketDataCache,
    MarketDataScheduler,
    CachedMarketData
)

client = TestClient(app)


class TestMarketDataCache:
    """Test MarketDataCache class."""
    
    def test_cache_initialization(self):
        """Test cache initializes with correct TTL."""
        cache = MarketDataCache(default_ttl_minutes=15)
        assert cache.default_ttl == timedelta(minutes=15)
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = MarketDataCache(default_ttl_minutes=30)
        
        data = {"price": 1500, "total": 100}
        cache.set("test_key", data, source="test")
        
        result = cache.get("test_key")
        assert result is not None
        assert result["price"] == 1500
        assert result["total"] == 100
        assert "cache_info" in result
    
    def test_cache_miss(self):
        """Test cache returns None for missing key."""
        cache = MarketDataCache(default_ttl_minutes=30)
        result = cache.get("non_existent_key")
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache marks data as stale after TTL."""
        cache = MarketDataCache(default_ttl_minutes=0)  # Expire immediately
        
        data = {"price": 1500}
        cache.set("test_key", data, source="test")
        
        # Should return stale data
        result = cache.get("test_key")
        assert result is not None
        assert result["cache_info"]["is_stale"] is True
    
    def test_cache_invalidate(self):
        """Test cache invalidation removes entry."""
        cache = MarketDataCache(default_ttl_minutes=30)
        
        cache.set("test_key", {"data": "value"}, source="test")
        assert cache.get("test_key") is not None
        
        cache.invalidate("test_key")
        assert cache.get("test_key") is None
    
    def test_cache_clear(self):
        """Test cache clear removes all entries."""
        cache = MarketDataCache(default_ttl_minutes=30)
        
        cache.set("key1", {"data": "value1"}, source="test")
        cache.set("key2", {"data": "value2"}, source="test")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = MarketDataCache(default_ttl_minutes=30)
        
        cache.set("key1", {"data": "value1"}, source="test")
        cache.set("key2", {"data": "value2"}, source="test")
        
        stats = cache.get_stats()
        
        assert stats["total_entries"] == 2
        assert "key1" in stats["entries"]
        assert "key2" in stats["entries"]
        assert "age_seconds" in stats["entries"]["key1"]


class TestCacheRouter:
    """Test cache router endpoints."""
    
    def test_cache_status_endpoint(self):
        """Test GET /cache/status endpoint."""
        response = client.get("/cache/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cache" in data
        assert "scheduler" in data
        assert "total_entries" in data["cache"]
        assert "is_running" in data["scheduler"]
    
    def test_cache_clear_endpoint(self):
        """Test POST /cache/clear endpoint."""
        response = client.post("/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "message" in data
    
    def test_cache_refresh_endpoint(self):
        """Test POST /cache/refresh endpoint."""
        response = client.post("/cache/refresh")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        assert "message" in data
    
    def test_cache_invalidate_endpoint(self):
        """Test DELETE /cache/{key} endpoint."""
        response = client.delete("/cache/test_key")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "test_key" in data["message"]
    
    def test_cache_get_endpoint_not_found(self):
        """Test GET /cache/{key} returns error for missing key."""
        # Clear cache first
        client.post("/cache/clear")
        
        response = client.get("/cache/non_existent_key")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "error" in data
        assert data["key"] == "non_existent_key"


class TestMarketDataScheduler:
    """Test MarketDataScheduler class."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initializes correctly."""
        cache = MarketDataCache(default_ttl_minutes=30)
        scheduler = MarketDataScheduler(
            cache=cache,
            refresh_interval_minutes=15,
            auto_start=False
        )
        
        assert scheduler.refresh_interval == 15
        assert scheduler.is_running is False
    
    def test_scheduler_status(self):
        """Test scheduler status."""
        cache = MarketDataCache(default_ttl_minutes=30)
        scheduler = MarketDataScheduler(
            cache=cache,
            refresh_interval_minutes=15,
            auto_start=False
        )
        
        status = scheduler.get_status()
        
        assert "is_running" in status
        assert "refresh_in_progress" in status
        assert "refresh_interval_minutes" in status
        assert status["refresh_interval_minutes"] == 15


class TestCachedMarketData:
    """Test CachedMarketData dataclass."""
    
    def test_cached_data_creation(self):
        """Test creating CachedMarketData instance."""
        data = {"price": 1500, "total": 100}
        cached = CachedMarketData(
            data=data,
            timestamp=datetime.now(),
            source="test",
            is_stale=False
        )
        
        assert cached.data == data
        assert cached.source == "test"
        assert cached.is_stale is False
    
    def test_cached_data_to_dict(self):
        """Test converting CachedMarketData to dict."""
        data = {"price": 1500}
        cached = CachedMarketData(
            data=data,
            timestamp=datetime.now(),
            source="test"
        )
        
        result = cached.to_dict()
        
        assert result["price"] == 1500
        assert "cache_info" in result
        assert result["cache_info"]["source"] == "test"
        assert "age_seconds" in result["cache_info"]

