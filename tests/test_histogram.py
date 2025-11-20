"""
Tests for histogram / price distribution functionality.
"""

import pytest
from app.services.histogram import get_price_distribution_summary


def test_price_distribution_basic():
    """Test basic price distribution calculation."""
    prices = [1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200]
    
    result = get_price_distribution_summary(prices)
    
    assert "histogram" in result
    assert "dominant_range" in result
    assert "dominant_percentage" in result
    
    # Check histogram structure
    assert isinstance(result["histogram"], list)
    assert len(result["histogram"]) > 0
    
    for bin in result["histogram"]:
        assert "start" in bin
        assert "end" in bin or bin["end"] is None
        assert "count" in bin
        assert "percentage" in bin
        assert "label" in bin


def test_price_distribution_empty():
    """Test distribution with empty price list."""
    prices = []
    
    result = get_price_distribution_summary(prices)
    
    assert result["histogram"] == []
    assert result["dominant_range"] is None
    assert result["dominant_percentage"] == 0.0


def test_price_distribution_single_price():
    """Test distribution with single price."""
    prices = [1800.0]
    
    result = get_price_distribution_summary(prices)
    
    assert len(result["histogram"]) > 0
    # Single price should fall into one bin
    total_count = sum(bin["count"] for bin in result["histogram"])
    assert total_count == 1


def test_price_distribution_dominant_range():
    """Test that dominant range is correctly identified."""
    # Most prices in 1800-2200 range
    prices = (
        [1500] * 5 +      # 5 in lower range
        [1900] * 30 +     # 30 in 1800-2200 (dominant)
        [2500] * 3        # 3 in higher range
    )
    
    result = get_price_distribution_summary(prices)
    
    # Dominant range should be where most prices are
    assert result["dominant_range"] is not None
    assert result["dominant_percentage"] > 70  # 30/38 ≈ 79%


def test_price_distribution_percentages():
    """Test that percentages sum to 100%."""
    prices = [1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 2200, 2300]
    
    result = get_price_distribution_summary(prices)
    
    total_percentage = sum(bin["percentage"] for bin in result["histogram"])
    
    # Should be close to 100% (allow small rounding errors)
    assert 99.0 <= total_percentage <= 101.0


def test_price_distribution_bins_ordered():
    """Test that histogram bins are in order."""
    prices = [1200, 1500, 1800, 2100, 2400, 2700]
    
    result = get_price_distribution_summary(prices)
    
    bins = result["histogram"]
    for i in range(len(bins) - 1):
        current_start = bins[i]["start"]
        next_start = bins[i + 1]["start"]
        assert current_start < next_start, "Bins should be ordered by start value"


def test_price_distribution_all_in_one_bin():
    """Test when all prices fall into same range."""
    # All prices in 1500-1800 range
    prices = [1550, 1600, 1650, 1700, 1750]
    
    result = get_price_distribution_summary(prices)
    
    # Should have one dominant bin with 100%
    assert result["dominant_percentage"] == 100.0


def test_price_distribution_edge_cases():
    """Test edge cases with very low and very high prices."""
    prices = [500, 1000, 1500, 2000, 2500, 3000, 5000]
    
    result = get_price_distribution_summary(prices)
    
    # Should handle extreme values
    assert len(result["histogram"]) > 0
    
    # First bin should include low price
    first_bin = result["histogram"][0]
    assert first_bin["start"] <= 500 or first_bin["count"] == 0
    
    # Last bin should include high price
    last_bin = result["histogram"][-1]
    assert last_bin["end"] is None or last_bin["end"] >= 5000


def test_price_distribution_real_world_data():
    """Test with realistic apartment price data."""
    # Simulated real market data
    prices = [
        1250, 1300, 1350, 1400, 1450,  # lower
        1500, 1550, 1600, 1650, 1700, 1750,  # mid-low
        1800, 1850, 1900, 1950, 2000, 2050,  # mid
        2100, 2150, 2200, 2250,  # mid-high
        2300, 2400, 2500,  # higher
        3000, 3500  # outliers
    ]
    
    result = get_price_distribution_summary(prices)
    
    # Should create reasonable distribution
    assert len(result["histogram"]) >= 5  # At least several bins
    
    # Total count should match
    total_count = sum(bin["count"] for bin in result["histogram"])
    assert total_count == len(prices)
    
    # Dominant range should be in middle somewhere
    assert result["dominant_range"] is not None
    assert "1800" in result["dominant_range"] or "2000" in result["dominant_range"] or "2200" in result["dominant_range"]


def test_price_distribution_bin_labels():
    """Test that bin labels are correctly formatted."""
    prices = [1500, 1600, 1700, 1800, 1900, 2000]
    
    result = get_price_distribution_summary(prices)
    
    for bin in result["histogram"]:
        label = bin["label"]
        
        # Label should be non-empty string
        assert isinstance(label, str)
        assert len(label) > 0
        
        # Should contain numbers or comparison symbols
        assert any(char.isdigit() or char in "<>-" for char in label)


def test_price_distribution_count_accuracy():
    """Test that counts in bins are accurate."""
    prices = [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800]
    
    result = get_price_distribution_summary(prices)
    
    # Sum of all bin counts should equal total prices
    total_count = sum(bin["count"] for bin in result["histogram"])
    assert total_count == len(prices)
    
    # No bin should have negative count
    for bin in result["histogram"]:
        assert bin["count"] >= 0

