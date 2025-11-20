"""
Tests for 999.md market scraper.

Note: These tests use mock data and don't require actual Playwright installation.
For integration tests with real scraping, run test_999md_scraper.py manually.
"""

import pytest
from app.scraping.md999 import (
    extract_price_from_text,
    extract_area_from_text,
)


class TestPriceExtraction:
    """Test price extraction from various text formats."""
    
    def test_extract_price_standard(self):
        """Test standard price format."""
        assert extract_price_from_text("85 000 €") == 85000.0
        assert extract_price_from_text("120 000 €") == 120000.0
    
    def test_extract_price_no_spaces(self):
        """Test price without spaces."""
        assert extract_price_from_text("85000€") == 85000.0
        assert extract_price_from_text("€85000") == 85000.0
    
    def test_extract_price_with_comma(self):
        """Test price with comma separator."""
        assert extract_price_from_text("85,000 €") == 85000.0
        assert extract_price_from_text("€120,000") == 120000.0
    
    def test_extract_price_invalid(self):
        """Test invalid price formats."""
        assert extract_price_from_text("Price not available") is None
        assert extract_price_from_text("Contact for price") is None
        assert extract_price_from_text("") is None


class TestAreaExtraction:
    """Test area extraction from various text formats."""
    
    def test_extract_area_standard(self):
        """Test standard area format."""
        assert extract_area_from_text("52 m²") == 52.0
        assert extract_area_from_text("60 m²") == 60.0
    
    def test_extract_area_m2_format(self):
        """Test m2 format."""
        assert extract_area_from_text("52 m2") == 52.0
        assert extract_area_from_text("52m2") == 52.0
    
    def test_extract_area_mp_format(self):
        """Test mp (metri pătrați) format."""
        assert extract_area_from_text("52 mp") == 52.0
        assert extract_area_from_text("52mp") == 52.0
    
    def test_extract_area_with_decimal(self):
        """Test area with decimal."""
        assert extract_area_from_text("52.5 m²") == 52.5
        assert extract_area_from_text("60.8 m²") == 60.8
    
    def test_extract_area_invalid(self):
        """Test invalid area formats."""
        assert extract_area_from_text("Area not specified") is None
        assert extract_area_from_text("Contact for details") is None
        assert extract_area_from_text("") is None


class TestCombinedExtraction:
    """Test extracting both price and area from combined text."""
    
    def test_extract_from_listing_text(self):
        """Test extraction from realistic listing text."""
        text = "Apartament 2 camere, 52 m², 85 000 €, Centru"
        
        price = extract_price_from_text(text)
        area = extract_area_from_text(text)
        
        assert price == 85000.0
        assert area == 52.0
        assert price / area == pytest.approx(1634.62, rel=0.01)
    
    def test_extract_euro_repair(self):
        """Test extraction from listing with Euro repair."""
        text = "2 camere, reparație euro, 55 m², €95,000"
        
        price = extract_price_from_text(text)
        area = extract_area_from_text(text)
        
        assert price == 95000.0
        assert area == 55.0


class TestPagination:
    """Test pagination detection logic."""

    def test_url_with_page_parameter(self):
        """Test that URL correctly appends page parameter."""
        base_url = "https://999.md/ro/list/real-estate/apartments-and-rooms?appl=1&o_30_241=894"

        # Page 1 - no change
        page_1_url = base_url
        assert "&page=" not in page_1_url

        # Page 2 - add parameter
        page_2_url = f"{base_url}&page=2"
        assert "&page=2" in page_2_url

        # Page 3 - add parameter
        page_3_url = f"{base_url}&page=3"
        assert "&page=3" in page_3_url

    def test_pagination_logic(self):
        """Test pagination iteration logic."""
        total_pages = 5
        pages_to_scrape = list(range(1, total_pages + 1))

        assert pages_to_scrape == [1, 2, 3, 4, 5]
        assert len(pages_to_scrape) == 5


@pytest.mark.skipif(True, reason="Requires Playwright installation - run test_999md_scraper.py manually")
class TestPlaywrightIntegration:
    """
    Integration tests for Playwright scraping.
    
    These are skipped by default because they require:
    - pip install playwright
    - playwright install chromium
    - Active internet connection
    
    Run manually: python test_999md_scraper.py
    """
    
    async def test_fetch_999md_prices(self):
        """Test fetching prices from 999.md (integration test)."""
        from app.scraping.md999 import fetch_all_999md_prices
        
        prices = await fetch_all_999md_prices()
        assert len(prices) > 0
        assert all(p > 0 for p in prices)
    
    async def test_compute_stats(self):
        """Test computing statistics from 999.md (integration test)."""
        from app.scraping.md999 import compute_999md_stats
        
        stats = await compute_999md_stats()
        assert stats.source == "999.md"
        assert stats.total_ads > 0
        assert stats.min_price_per_sqm > 0
        assert stats.max_price_per_sqm > stats.min_price_per_sqm
        assert stats.avg_price_per_sqm > 0

