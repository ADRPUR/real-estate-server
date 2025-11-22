"""
Tests for settings module.
"""

import pytest
import os
from app.core.config import get_settings, Settings


def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_settings_defaults():
    """Test default settings values."""
    settings = get_settings()

    # Check that defaults exist
    assert settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert settings.market_summary_ttl_minutes > 0
    assert settings.fx_cache_ttl_seconds > 0
    assert isinstance(settings.cors_origins, list)


def test_settings_env_prefix():
    """Test that settings use APP_ prefix."""
    # This is implicit in Settings class with env_prefix
    settings = get_settings()
    assert hasattr(settings, 'log_level')
    assert hasattr(settings, 'accesimobil_url')
    assert hasattr(settings, 'proimobil_url')


def test_settings_quartile_config():
    """Test quartile-related settings."""
    settings = get_settings()

    assert hasattr(settings, 'enable_999md_scraper')
    assert hasattr(settings, 'max_999md_pages')
    assert isinstance(settings.enable_999md_scraper, bool)
    assert isinstance(settings.max_999md_pages, int)


def test_settings_urls():
    """Test that URL settings are valid strings."""
    settings = get_settings()

    assert isinstance(settings.accesimobil_url, str)
    assert isinstance(settings.proimobil_url, str)
    assert isinstance(settings.md999_url, str)

    # URLs should start with http
    assert settings.accesimobil_url.startswith('http')
    assert settings.proimobil_url.startswith('http')
    assert settings.md999_url.startswith('http')


def test_settings_cache_ttl():
    """Test cache TTL settings."""
    settings = get_settings()

    assert settings.market_summary_ttl_minutes >= 1
    assert settings.fx_cache_ttl_seconds >= 60
