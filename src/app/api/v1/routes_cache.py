"""
Cache management router - endpoints for monitoring and controlling the cache.
"""

from fastapi import APIRouter
from app.services.cache import (
    get_market_cache,
    get_market_scheduler
)

router = APIRouter(prefix='/cache', tags=['cache'])


@router.get('/status')
async def cache_status():
    """
    Get cache status and statistics.
    
    Returns:
    - Cache statistics (entries, age, expiration status)
    - Scheduler status (is running, next run time)
    """
    cache = get_market_cache()
    scheduler = get_market_scheduler()
    
    return {
        "cache": cache.get_stats(),
        "scheduler": scheduler.get_status()
    }


@router.post('/refresh')
async def trigger_refresh():
    """
    Manually trigger a cache refresh immediately.
    
    This will scrape all data sources and update the cache.
    Returns immediately - the refresh runs in the background.
    """
    scheduler = get_market_scheduler()
    started = scheduler.trigger_refresh_now()
    
    return {
        "success": started,
        "message": "Refresh started" if started else "Refresh already in progress"
    }


@router.post('/clear')
async def clear_cache():
    """
    Clear all cached data.
    
    Next requests will trigger fresh scraping.
    """
    cache = get_market_cache()
    cache.clear()
    
    return {
        "success": True,
        "message": "Cache cleared"
    }


@router.delete('/{key}')
async def invalidate_cache_key(key: str):
    """
    Invalidate a specific cache key.
    
    Args:
        key: Cache key to invalidate (e.g., 'proimobil_api', 'accesimobil', '999md')
    """
    cache = get_market_cache()
    cache.invalidate(key)
    
    return {
        "success": True,
        "message": f"Cache key '{key}' invalidated"
    }


@router.get('/{key}')
async def get_cached_data(key: str):
    """
    Get cached data for a specific key.
    
    Args:
        key: Cache key (e.g., 'proimobil_api', 'accesimobil', '999md')
    
    Returns:
        Cached data with metadata, or 404 if not found
    """
    cache = get_market_cache()
    data = cache.get(key)
    
    if data is None:
        return {
            "error": "Not found",
            "key": key,
            "message": f"No cached data for key '{key}'"
        }
    
    return {
        "key": key,
        "data": data
    }

