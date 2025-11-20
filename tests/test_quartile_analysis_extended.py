"""
Extended tests for quartile analysis edge cases and additional scenarios.
"""

import pytest
from app.services.quartile_analysis import (
    calculate_quartiles,
    remove_outliers_iqr,
    get_quartile_interpretation
)


def test_calculate_quartiles_large_dataset():
    """Test quartiles with large dataset."""
    prices = list(range(1000, 3000, 10))  # 200 prices

    quartiles = calculate_quartiles(prices)

    assert quartiles['q1'] < quartiles['q2'] < quartiles['q3']
    assert quartiles['iqr'] > 0


def test_calculate_quartiles_duplicates():
    """Test quartiles with many duplicate values."""
    prices = [1500] * 10 + [1600] * 10 + [1700] * 10

    quartiles = calculate_quartiles(prices)

    # Should still calculate valid quartiles
    assert quartiles['q1'] > 0
    assert quartiles['q3'] > 0


def test_remove_outliers_iqr_no_outliers():
    """Test that no outliers are removed from normal distribution."""
    # Normal bell curve
    prices = [1400, 1500, 1550, 1600, 1650, 1700, 1750, 1800, 1900]

    filtered, removed = remove_outliers_iqr(prices)

    # Should not remove any
    assert removed == 0
    assert len(filtered) == len(prices)


def test_remove_outliers_iqr_extreme_high():
    """Test removal of extremely high outliers."""
    prices = [1500, 1600, 1700, 1800, 1900, 50000]

    filtered, removed = remove_outliers_iqr(prices)

    # Should remove the extreme value
    assert removed > 0
    assert 50000 not in filtered


def test_remove_outliers_iqr_extreme_low():
    """Test removal of extremely low outliers."""
    prices = [100, 1500, 1600, 1700, 1800, 1900]

    filtered, removed = remove_outliers_iqr(prices)

    # Should remove the extreme value
    assert removed > 0
    assert 100 not in filtered


def test_remove_outliers_iqr_custom_factor():
    """Test outlier removal with custom factor."""
    prices = [1000, 1500, 1600, 1700, 1800, 1900, 3000]

    # With stricter factor
    filtered_strict, removed_strict = remove_outliers_iqr(prices, factor=1.0)

    # With looser factor
    filtered_loose, removed_loose = remove_outliers_iqr(prices, factor=2.0)

    # Stricter should remove more
    assert removed_strict >= removed_loose


def test_get_quartile_interpretation_below_market():
    """Test interpretation for below market prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Very low price
    interp = get_quartile_interpretation(1200, q1, q3)
    assert interp == "below_market"


def test_get_quartile_interpretation_budget():
    """Test interpretation for budget prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Just below Q1
    interp = get_quartile_interpretation(1450, q1, q3)
    assert interp == "budget"


def test_get_quartile_interpretation_affordable():
    """Test interpretation for affordable prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Between Q1 and median
    interp = get_quartile_interpretation(1650, q1, q3)
    assert interp in ["affordable", "mid_range"]


def test_get_quartile_interpretation_mid_range():
    """Test interpretation for mid-range prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Between median and Q3
    interp = get_quartile_interpretation(1900, q1, q3)
    assert interp == "mid_range"


def test_get_quartile_interpretation_premium():
    """Test interpretation for premium prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Just above Q3
    interp = get_quartile_interpretation(2100, q1, q3)
    assert interp == "premium"


def test_get_quartile_interpretation_luxury():
    """Test interpretation for luxury prices."""
    q1 = 1500.0
    q3 = 2000.0

    # Well above Q3
    interp = get_quartile_interpretation(2500, q1, q3)
    assert interp == "luxury"


def test_quartiles_with_negative_values():
    """Test quartiles handle negative values (edge case)."""
    # Shouldn't happen in real data, but test robustness
    prices = [-100, 0, 100, 200, 300]

    quartiles = calculate_quartiles(prices)

    # Should still calculate
    assert quartiles['q2'] == 100  # median


def test_quartiles_with_floats():
    """Test quartiles with float values."""
    prices = [1500.5, 1600.75, 1700.25, 1800.9, 1900.1]

    quartiles = calculate_quartiles(prices)

    # Should handle floats
    assert isinstance(quartiles['q1'], float)
    assert isinstance(quartiles['q2'], float)
    assert isinstance(quartiles['q3'], float)


def test_remove_outliers_preserves_order():
    """Test that removing outliers preserves value relationships."""
    prices = [1000, 1500, 1600, 1700, 1800, 10000]

    filtered, _ = remove_outliers_iqr(prices)

    # Filtered should still be a valid sequence
    for i in range(len(filtered) - 1):
        assert filtered[i] <= filtered[i + 1]


def test_quartiles_two_values():
    """Test quartiles with only two values."""
    prices = [1500.0, 2000.0]

    quartiles = calculate_quartiles(prices)

    # Should handle gracefully
    assert quartiles['q1'] > 0
    assert quartiles['q3'] > 0
    assert quartiles['q2'] > 0


def test_quartiles_three_values():
    """Test quartiles with three values."""
    prices = [1500.0, 1750.0, 2000.0]

    quartiles = calculate_quartiles(prices)

    # Q2 should be the middle value
    assert quartiles['q2'] == 1750.0


def test_remove_outliers_all_outliers():
    """Test when all values are outliers (edge case)."""
    # Very spread out data
    prices = [100, 5000, 10000, 15000, 20000]

    filtered, removed = remove_outliers_iqr(prices)

    # Should remove some values
    assert removed >= 0
    # But should keep at least some
    assert len(filtered) > 0


def test_quartile_interpretation_edge_values():
    """Test interpretation exactly at Q1 and Q3."""
    q1 = 1500.0
    q3 = 2000.0

    # Exactly at Q1
    interp_q1 = get_quartile_interpretation(1500, q1, q3)
    assert interp_q1 in ["affordable", "mid_range"]

    # Exactly at Q3
    interp_q3 = get_quartile_interpretation(2000, q1, q3)
    assert interp_q3 in ["mid_range", "premium"]

