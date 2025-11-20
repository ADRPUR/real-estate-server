"""
Tests for quartile analysis functionality.
"""

import pytest
from app.services.quartile_analysis import (
    calculate_quartiles,
    remove_outliers_iqr,
    get_quartile_interpretation
)


def test_calculate_quartiles_normal_distribution():
    """Test quartile calculation with normal distribution."""
    prices = [1200, 1400, 1500, 1600, 1700, 1800, 2000, 2200, 2400]
    
    quartiles = calculate_quartiles(prices)
    
    assert 'q1' in quartiles
    assert 'q2' in quartiles
    assert 'q3' in quartiles
    assert 'iqr' in quartiles
    
    # Q1 should be around 25th percentile
    assert 1400 <= quartiles['q1'] <= 1600
    
    # Q2 (median) should be middle value
    assert quartiles['q2'] == 1700
    
    # Q3 should be around 75th percentile
    assert 1900 <= quartiles['q3'] <= 2200
    
    # IQR should be Q3 - Q1
    assert quartiles['iqr'] == quartiles['q3'] - quartiles['q1']


def test_calculate_quartiles_small_dataset():
    """Test quartile calculation with small dataset."""
    prices = [1500, 1600, 1700]
    
    quartiles = calculate_quartiles(prices)
    
    # Should still return valid quartiles
    assert quartiles['q1'] > 0
    assert quartiles['q2'] == 1600  # median
    assert quartiles['q3'] > quartiles['q1']


def test_calculate_quartiles_single_value():
    """Test quartile calculation with single value."""
    prices = [1500.0]
    
    quartiles = calculate_quartiles(prices)
    
    # All quartiles should be the same
    assert quartiles['q1'] == 1500.0
    assert quartiles['q2'] == 1500.0
    assert quartiles['q3'] == 1500.0
    assert quartiles['iqr'] == 0.0


def test_calculate_quartiles_empty():
    """Test quartile calculation with empty list."""
    prices = []
    
    quartiles = calculate_quartiles(prices)
    
    # Should return zeros
    assert quartiles['q1'] == 0.0
    assert quartiles['q2'] == 0.0
    assert quartiles['q3'] == 0.0
    assert quartiles['iqr'] == 0.0


def test_remove_outliers_iqr_with_outliers():
    """Test outlier removal with clear outliers."""
    # Create data with obvious outliers (factor 1.5 means outliers are 1.5*IQR beyond Q1/Q3)
    prices = [1000, 1500, 1600, 1700, 1800, 1900, 2000, 2100, 8000, 10000]

    filtered, num_removed = remove_outliers_iqr(prices)
    
    # Should remove the extreme values (8000, 10000)
    assert num_removed > 0
    assert len(filtered) < len(prices)
    # The very extreme outliers should be removed
    assert 10000 not in filtered


def test_remove_outliers_iqr_no_outliers():
    """Test outlier removal with no outliers."""
    # Normal distribution without outliers
    prices = [1500, 1600, 1700, 1800, 1900, 2000]
    
    filtered, num_removed = remove_outliers_iqr(prices)
    
    # Should not remove any values
    assert num_removed == 0
    assert len(filtered) == len(prices)


def test_remove_outliers_iqr_small_dataset():
    """Test outlier removal with small dataset."""
    prices = [1500, 1600, 1700]
    
    filtered, num_removed = remove_outliers_iqr(prices)
    
    # Should return original data (too small to detect outliers reliably)
    assert filtered == prices
    assert num_removed == 0


def test_get_quartile_interpretation():
    """Test quartile interpretation function."""
    q1 = 1500.0
    q3 = 2000.0
    
    # Test different price points
    assert get_quartile_interpretation(1200, q1, q3) == "below_market"  # < Q1 * 0.85
    assert get_quartile_interpretation(1400, q1, q3) == "budget"  # < Q1
    assert get_quartile_interpretation(1600, q1, q3) == "affordable"  # Q1 to median
    assert get_quartile_interpretation(1800, q1, q3) == "mid_range"  # median to Q3
    assert get_quartile_interpretation(2050, q1, q3) == "premium"  # just above Q3
    assert get_quartile_interpretation(2500, q1, q3) == "luxury"  # well above Q3


def test_quartiles_real_world_data():
    """Test with realistic apartment price data."""
    # Simulated real-world data from market
    prices = [
        1250, 1300, 1350, 1400, 1450,  # lower range
        1500, 1550, 1600, 1650, 1700,  # mid-lower
        1750, 1800, 1850, 1900, 1950,  # mid-upper
        2000, 2100, 2200, 2300, 2400,  # upper range
        3000, 5000  # outliers (old listings, premium locations)
    ]
    
    quartiles = calculate_quartiles(prices)
    
    # Q1 should be around lower-mid range
    assert 1400 <= quartiles['q1'] <= 1700
    
    # Median should be mid range
    assert 1700 <= quartiles['q2'] <= 1900
    
    # Q3 should be upper-mid range
    assert 1900 <= quartiles['q3'] <= 2300
    
    # IQR should be reasonable
    assert 400 <= quartiles['iqr'] <= 800
    
    # Remove outliers and recalculate
    filtered, num_removed = remove_outliers_iqr(prices)
    
    # Should remove the extreme values
    assert num_removed >= 1
    assert 5000 not in filtered


def test_quartiles_precision():
    """Test that quartiles are rounded to 2 decimal places."""
    prices = [1234.567, 1345.678, 1456.789, 1567.890]
    
    quartiles = calculate_quartiles(prices)
    
    # Check that values are rounded to 2 decimals
    assert quartiles['q1'] == round(quartiles['q1'], 2)
    assert quartiles['q2'] == round(quartiles['q2'], 2)
    assert quartiles['q3'] == round(quartiles['q3'], 2)
    assert quartiles['iqr'] == round(quartiles['iqr'], 2)

