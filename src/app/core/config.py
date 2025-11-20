"""Centralized application settings using Pydantic.
Environment variable prefix: APP_

Override examples:
  export APP_MARKET_SUMMARY_TTL_MINUTES=30
  export APP_LOG_LEVEL=DEBUG
  export APP_CORS_ORIGINS='["http://localhost:5173","https://example.com"]'
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    # Market URLs
    accesimobil_url: str = Field("https://accesimobil.md/apartamente-vanzare?fi1[]=8&fi2[]=72", description="Base URL for Accesimobil scraping")
    proimobil_url: str = Field("https://proimobil.md/apartamente-de-vanzare-in-chisinau?filter=offer%3Asell%3Bcategory%3Aapartment%3BregionId%3Ac06c894d-a8f5-4744-a312-fb0c376983c3%3Bsurface%3A40..60%3Brooms%3A2%3Bcondition%3Anew%3BapartmentState%3Aeuro", description="Base URL for Proimobil scraping")
    md999_url: str = Field("https://999.md/ro/list/real-estate/apartments-and-rooms?appl=1&o_30_241=894&ef=16,9441,32,30,2307,1073&eo=13859,12885,12900,12912&o_16_1=776&o_32_9_12900_13859=15667&from_1073_244=40&to_1073_244=60", description="Base URL for 999.md scraping")

    # Cache Settings
    cache_ttl_minutes: int = Field(30, description="TTL for market data cache in minutes")
    scraping_interval_minutes: int = Field(30, description="Interval for automatic scraping refresh in minutes")
    market_summary_ttl_minutes: int = Field(15, description="TTL for /market/summary cache in minutes")
    fx_cache_ttl_seconds: int = Field(1800, description="TTL for FX rates cache (seconds)")

    # Logging
    log_level: str = Field("INFO", description="Root log level")

    # CORS
    cors_origins: List[str] = Field(default_factory=lambda: [
        "http://localhost:5173", "http://127.0.0.1:5173"
    ], description="Allowed CORS origins")

    # 999.md Scraper Settings
    enable_999md_scraper: bool = Field(False, description="Enable dynamic 999.md scraping (requires Selenium/webdriver-manager). Set APP_ENABLE_999MD_SCRAPER=True to enable.")
    max_999md_pages: int = Field(3, description="Maximum number of pages to scrape from 999.md when enabled")
    playwright_use_system_chromium: bool = Field(False, description="Use system Chromium executable instead of Playwright-managed browser if downloads fail")
    playwright_chromium_executable: Optional[str] = Field(None, description="Path to system Chromium (e.g. /usr/bin/chromium-browser). Used when playwright_use_system_chromium=True")


    model_config = {
        "env_prefix": "APP_",
        "case_sensitive": False,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
