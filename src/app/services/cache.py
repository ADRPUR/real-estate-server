"""
Market data cache and scheduler for periodic scraping.

This module provides:
1. In-memory cache for market data (can be easily migrated to Redis/Postgres)
2. Background scheduler for periodic data refresh
3. Cache TTL and invalidation mechanisms
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from threading import Lock
import asyncio
from dataclasses import dataclass, asdict

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


@dataclass
class CachedMarketData:
    """Cached market statistics data."""
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    is_stale: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = self.data.copy()
        result['cache_info'] = {
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'is_stale': self.is_stale,
            'age_seconds': (datetime.now() - self.timestamp).total_seconds()
        }
        return result


class MarketDataCache:
    """
    Thread-safe cache for market data with TTL support.
    
    Can be easily migrated to Redis by replacing the storage backend.
    """
    
    def __init__(self, default_ttl_minutes: int = 30):
        """
        Initialize cache.
        
        Args:
            default_ttl_minutes: Default TTL for cache entries in minutes
        """
        self._cache: Dict[str, CachedMarketData] = {}
        self._lock = Lock()
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        logger.info(f"MarketDataCache initialized with TTL={default_ttl_minutes} minutes")
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key.
        
        Args:
            key: Cache key (e.g., 'proimobil_api', 'accesimobil', 'market_summary')
        
        Returns:
            Cached data dict with cache_info, or None if not found/expired
        """
        with self._lock:
            cached = self._cache.get(key)
            
            if cached is None:
                logger.debug(f"Cache MISS for key: {key}")
                return None
            
            # Check if expired
            age = datetime.now() - cached.timestamp
            if age > self.default_ttl:
                logger.info(f"Cache EXPIRED for key: {key} (age: {age.total_seconds():.1f}s)")
                cached.is_stale = True
                return cached.to_dict()  # Return stale data with flag
            
            logger.debug(f"Cache HIT for key: {key} (age: {age.total_seconds():.1f}s)")
            return cached.to_dict()
    
    def set(self, key: str, data: Dict[str, Any], source: str = "unknown"):
        """
        Store data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            source: Source identifier for logging
        """
        with self._lock:
            cached = CachedMarketData(
                data=data,
                timestamp=datetime.now(),
                source=source,
                is_stale=False
            )
            self._cache[key] = cached
            logger.info(f"Cache SET for key: {key} (source: {source})")
    
    def invalidate(self, key: str):
        """
        Invalidate (remove) cached data.
        
        Args:
            key: Cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Cache INVALIDATED for key: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache CLEARED ({count} entries removed)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            stats = {
                'total_entries': len(self._cache),
                'entries': {}
            }
            
            for key, cached in self._cache.items():
                age = datetime.now() - cached.timestamp
                is_expired = age > self.default_ttl
                
                stats['entries'][key] = {
                    'timestamp': cached.timestamp.isoformat(),
                    'age_seconds': age.total_seconds(),
                    'age_minutes': age.total_seconds() / 60,
                    'is_expired': is_expired,
                    'is_stale': cached.is_stale,
                    'source': cached.source
                }
            
            return stats


class MarketDataScheduler:
    """
    Background scheduler for periodic market data scraping.
    
    Runs scraping tasks at configurable intervals and updates cache.
    """
    
    def __init__(
        self,
        cache: MarketDataCache,
        refresh_interval_minutes: int = 30,
        auto_start: bool = True
    ):
        """
        Initialize scheduler.
        
        Args:
            cache: MarketDataCache instance to update
            refresh_interval_minutes: How often to refresh data (minutes)
            auto_start: Whether to start scheduler immediately
        """
        self.cache = cache
        self.refresh_interval = refresh_interval_minutes
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._refresh_in_progress = False
        self._lock = Lock()
        
        logger.info(f"MarketDataScheduler initialized (interval={refresh_interval_minutes}min)")
        
        if auto_start:
            self.start()
    
    def start(self):
        """Start the background scheduler."""
        if self.is_running:
            logger.warning("Scheduler already running")
            return
        
        # Schedule periodic refresh
        self.scheduler.add_job(
            func=self._refresh_all_market_data,
            trigger=IntervalTrigger(minutes=self.refresh_interval),
            id='market_data_refresh',
            name='Market Data Refresh',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"Scheduler STARTED - will refresh every {self.refresh_interval} minutes")
        
        # Do initial refresh immediately (in background)
        asyncio.create_task(self._async_initial_refresh())
    
    async def _async_initial_refresh(self):
        """Do initial refresh asynchronously."""
        logger.info("Starting initial data refresh...")
        await asyncio.sleep(1)  # Small delay to let server start
        self._refresh_all_market_data()
    
    def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("Scheduler STOPPED")
    
    def _refresh_all_market_data(self):
        """
        Refresh all market data sources.
        
        This runs in a background thread by APScheduler.
        """
        with self._lock:
            if self._refresh_in_progress:
                logger.warning("Refresh already in progress, skipping")
                return
            
            self._refresh_in_progress = True
        
        try:
            logger.info("="*60)
            logger.info("Starting scheduled market data refresh...")
            logger.info("="*60)
            
            # Import here to avoid circular imports
            from app.services.proimobil_api_service import compute_proimobil_api_stats
            from app.scraping.accesimobil import compute_stats_for_accesimobil
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # 1. Refresh Proimobil API data (stats + listings)
            logger.info("Refreshing Proimobil API data...")
            try:
                from app.services.proimobil_api_service import get_detailed_proimobil_api_listings

                # Refresh stats
                proimobil_stats = compute_proimobil_api_stats(max_items=1000)
                self.cache.set('proimobil_api', asdict(proimobil_stats), source='scheduler')
                logger.info(f"✓ Proimobil API stats: {proimobil_stats.total_ads} ads")

                # Refresh detailed listings
                proimobil_listings = get_detailed_proimobil_api_listings(max_items=1000)
                listings_data = {
                    "total": len(proimobil_listings),
                    "listings": proimobil_listings
                }
                self.cache.set('proimobil_api_listings', listings_data, source='scheduler')
                logger.info(f"✓ Proimobil API listings: {len(proimobil_listings)} listings cached")
            except Exception as e:
                logger.error(f"✗ Proimobil API refresh failed: {e}")
            
            # 2. Refresh Accesimobil data
            logger.info("Refreshing Accesimobil data...")
            try:
                accesimobil_stats = compute_stats_for_accesimobil(settings.accesimobil_url)
                self.cache.set('accesimobil', asdict(accesimobil_stats), source='scheduler')
                logger.info(f"✓ Accesimobil: {accesimobil_stats.total_ads} ads")
            except Exception as e:
                logger.error(f"✗ Accesimobil refresh failed: {e}")
            
            # 3. Refresh 999.md data (if enabled)
            if settings.enable_999md_scraper:
                logger.info("Refreshing 999.md data...")
                try:
                    from app.scraping.md999 import compute_999md_stats
                    import asyncio
                    
                    # Run async function in sync context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    md999_stats = loop.run_until_complete(compute_999md_stats(settings.md999_url))
                    loop.close()
                    
                    self.cache.set('999md', asdict(md999_stats), source='scheduler')
                    logger.info(f"✓ 999.md: {md999_stats.total_ads} ads")
                except Exception as e:
                    logger.error(f"✗ 999.md refresh failed: {e}")
            
            logger.info("="*60)
            logger.info("Market data refresh completed!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error during market data refresh: {e}", exc_info=True)
        
        finally:
            with self._lock:
                self._refresh_in_progress = False
    
    def trigger_refresh_now(self):
        """
        Trigger an immediate refresh (manual override).
        
        Returns:
            bool: True if refresh started, False if already in progress
        """
        if self._refresh_in_progress:
            logger.warning("Refresh already in progress")
            return False
        
        logger.info("Manual refresh triggered")
        self._refresh_all_market_data()
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run': job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        return {
            'is_running': self.is_running,
            'refresh_in_progress': self._refresh_in_progress,
            'refresh_interval_minutes': self.refresh_interval,
            'jobs': jobs
        }


# Global instances (singleton pattern)
_cache_instance: Optional[MarketDataCache] = None
_scheduler_instance: Optional[MarketDataScheduler] = None


def get_market_cache() -> MarketDataCache:
    """Get the global cache instance (singleton)."""
    global _cache_instance
    if _cache_instance is None:
        from app.core.config import get_settings
        settings = get_settings()
        ttl = getattr(settings, 'cache_ttl_minutes', 30)
        _cache_instance = MarketDataCache(default_ttl_minutes=ttl)
    return _cache_instance


def get_market_scheduler() -> MarketDataScheduler:
    """Get the global scheduler instance (singleton)."""
    global _scheduler_instance
    if _scheduler_instance is None:
        from app.core.config import get_settings
        settings = get_settings()
        interval = getattr(settings, 'scraping_interval_minutes', 30)
        cache = get_market_cache()
        _scheduler_instance = MarketDataScheduler(
            cache=cache,
            refresh_interval_minutes=interval,
            auto_start=True
        )
    return _scheduler_instance


def init_cache_and_scheduler():
    """Initialize cache and scheduler (call on app startup)."""
    logger.info("Initializing market data cache and scheduler...")
    get_market_cache()
    get_market_scheduler()
    logger.info("Cache and scheduler initialized!")

