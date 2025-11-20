import pytest
from app.domain.market_utils import build_price_histogram, get_price_distribution_summary


def test_build_price_histogram_basic():
    """Test basic histogram with sample prices"""
    prices = [1400, 1600, 1800, 2100, 2300, 2500, 2700, 2900, 3200]
    histogram = build_price_histogram(prices)
    
    assert len(histogram) > 0
    assert all(bin.count >= 0 for bin in histogram)
    assert all(0 <= bin.percentage <= 100 for bin in histogram)
    
    # Total percentage should be ~100%
    total_percentage = sum(bin.percentage for bin in histogram)
    assert 99 <= total_percentage <= 101


def test_build_price_histogram_empty():
    """Test histogram with empty price list"""
    histogram = build_price_histogram([])
    assert histogram == []


def test_get_price_distribution_summary():
    """Test price distribution summary"""
    prices = [1400, 1600, 1800, 2100, 2300, 2500, 2700, 2900, 3200, 3400]
    summary = get_price_distribution_summary(prices)
    
    assert summary["total_ads"] == 10
    assert len(summary["histogram"]) > 0
    assert summary["dominant_range"] is not None
    assert summary["dominant_percentage"] > 0


def test_histogram_fixed_intervals():
    """Test that histogram uses fixed intervals"""
    prices = [1450, 1750, 2250, 2750, 3250, 3750]
    histogram = build_price_histogram(prices)
    
    # Verify predefined intervals
    labels = [bin.label for bin in histogram]
    expected_labels = ["<1300", "1300-1600", "1600-1900", "1900-2200", "2200-2500", "2500-3000", ">3000"]

    # Should have intervals up to 3000 even if empty
    for label in ["<1300", "1300-1600", "1600-1900", "1900-2200", "2200-2500", "2500-3000"]:
        assert label in labels


def test_histogram_percentages_sum_to_100():
    """Test that percentages sum to approximately 100%"""
    prices = [1500, 1700, 1900, 2100, 2300, 2500, 2700, 2900, 3100, 3300]
    summary = get_price_distribution_summary(prices)
    
    total_percentage = sum(bin.percentage for bin in summary["histogram"])
    assert 99.5 <= total_percentage <= 100.5


def test_dominant_range_detection():
    """Test that dominant range is correctly identified"""
    # Create prices with clear dominant range in 1900-2200
    prices = [2000] * 10 + [1400] * 2 + [3200] * 3
    summary = get_price_distribution_summary(prices)
    
    assert summary["dominant_range"] == "1900-2200"
    assert summary["dominant_percentage"] > 50  # Should be 10/15 = 66.7%


def test_histogram_boundary_values():
    """Test prices exactly on boundaries"""
    prices = [1500, 2000, 2500, 3000, 3500]
    histogram = build_price_histogram(prices)
    
    # Each price should be counted in the correct bin
    total_count = sum(bin.count for bin in histogram)
    assert total_count == len(prices)


def test_single_price_value():
    """Test histogram with only one unique price"""
    prices = [2000] * 5
    summary = get_price_distribution_summary(prices)
    
    # All prices should be in one bin
    assert summary["dominant_percentage"] == 100.0
    assert summary["total_ads"] == 5


def test_empty_prices_summary():
    """Test summary with empty prices."""
    summary = get_price_distribution_summary([])

    assert summary["total_ads"] == 0
    assert summary["histogram"] == []
    assert summary["dominant_range"] is None
    assert summary["dominant_percentage"] == 0.0


def test_prices_in_single_range():
    """Test prices all in single range."""
    prices = [1950, 2000, 2050, 2100, 2150]
    summary = get_price_distribution_summary(prices)

    assert summary["total_ads"] == 5
    assert summary["dominant_percentage"] == 100.0
    assert summary["dominant_range"] == "1900-2200"  # All prices fall in 1900-2200 interval
