"""
Quartile analysis utilities for market statistics.

Provides functions to calculate quartiles (Q1, Q2, Q3) and IQR
for eliminating outliers and understanding realistic price ranges.
"""

from typing import List, Dict, Tuple
import statistics


def calculate_quartiles(prices: List[float]) -> Dict[str, float]:
    """
    Calculate quartile statistics for a list of prices.
    
    Args:
        prices: List of price values (e.g., price per sqm)
        
    Returns:
        Dictionary containing:
        - q1: 25th percentile (preț minim realist)
        - q2: 50th percentile (median)
        - q3: 75th percentile (zona premium)
        - iqr: Interquartile Range (Q3 - Q1) - cât de largă e piața reală
        
    Example:
        >>> prices = [1200, 1400, 1500, 1600, 1800, 2000, 2200]
        >>> stats = calculate_quartiles(prices)
        >>> print(stats['q1'])  # ~1400
        >>> print(stats['q3'])  # ~2000
        >>> print(stats['iqr'])  # ~600
    """
    if not prices:
        return {
            'q1': 0.0,
            'q2': 0.0,
            'q3': 0.0,
            'iqr': 0.0,
        }
    
    if len(prices) == 1:
        val = prices[0]
        return {
            'q1': val,
            'q2': val,
            'q3': val,
            'iqr': 0.0,
        }
    
    sorted_prices = sorted(prices)
    
    # Using statistics.quantiles (available in Python 3.8+)
    # quantiles(data, n=4) returns 3 cut points: Q1, Q2 (median), Q3
    try:
        q1, q2, q3 = statistics.quantiles(sorted_prices, n=4)
    except statistics.StatisticsError:
        # Fallback for edge cases
        q1 = sorted_prices[len(sorted_prices) // 4]
        q2 = statistics.median(sorted_prices)
        q3 = sorted_prices[3 * len(sorted_prices) // 4]
    
    iqr = q3 - q1
    
    return {
        'q1': round(q1, 2),
        'q2': round(q2, 2),
        'q3': round(q3, 2),
        'iqr': round(iqr, 2),
    }


def remove_outliers_iqr(prices: List[float], factor: float = 1.5) -> Tuple[List[float], int]:
    """
    Remove outliers using the IQR method.
    
    Outliers are defined as values outside the range:
    [Q1 - factor * IQR, Q3 + factor * IQR]
    
    Standard factor is 1.5 (Tukey's fences).
    
    Args:
        prices: List of price values
        factor: IQR multiplier for outlier detection (default: 1.5)
        
    Returns:
        Tuple of (filtered_prices, num_outliers_removed)
        
    Example:
        >>> prices = [1000, 1500, 1600, 1700, 1800, 5000]  # 5000 is outlier
        >>> filtered, removed = remove_outliers_iqr(prices)
        >>> len(filtered)  # 5
        >>> removed  # 1
    """
    if len(prices) < 4:
        return prices, 0
    
    quartiles = calculate_quartiles(prices)
    q1 = quartiles['q1']
    q3 = quartiles['q3']
    iqr = quartiles['iqr']
    
    # Define bounds for outliers
    lower_bound = q1 - factor * iqr
    upper_bound = q3 + factor * iqr
    
    # Filter prices
    filtered_prices = [p for p in prices if lower_bound <= p <= upper_bound]
    num_removed = len(prices) - len(filtered_prices)
    
    return filtered_prices, num_removed


def get_quartile_interpretation(price: float, q1: float, q3: float) -> str:
    """
    Get human-readable interpretation of where a price falls in the quartile range.
    
    Args:
        price: Price to interpret
        q1: First quartile (25th percentile)
        q3: Third quartile (75th percentile)
        
    Returns:
        String description: "below_market", "affordable", "mid_range", "premium", "luxury"
    """
    if price < q1 * 0.85:
        return "below_market"  # Suspiciously low
    elif price < q1:
        return "budget"  # Below Q1
    elif price < (q1 + q3) / 2:
        return "affordable"  # Q1 to median
    elif price < q3:
        return "mid_range"  # Median to Q3
    elif price < q3 * 1.15:
        return "premium"  # Just above Q3
    else:
        return "luxury"  # Well above Q3


__all__ = [
    'calculate_quartiles',
    'remove_outliers_iqr',
    'get_quartile_interpretation',
]

