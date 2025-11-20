# Compatibility shim for legacy histogram utilities
from typing import List, Dict
from app.domain.market_stats import HistogramBin

# Legacy intervals expected by tests
_LEGACY_INTERVALS = [
    (0, 1300, "<1300"),
    (1300, 1600, "1300-1600"),
    (1600, 1900, "1600-1900"),
    (1900, 2200, "1900-2200"),
    (2200, 2500, "2200-2500"),
    (2500, 3000, "2500-3000"),
    (3000, None, ">3000"),
]

def build_price_histogram(prices_per_sqm: List[float]) -> List[HistogramBin]:
    if not prices_per_sqm:
        return []
    total = len(prices_per_sqm)
    histogram: List[HistogramBin] = []
    for start, end, label in _LEGACY_INTERVALS:
        if end is None:
            count = sum(1 for price in prices_per_sqm if price >= start)
        else:
            count = sum(1 for price in prices_per_sqm if start <= price < end)
        # Keep empty bins below 3000 as per original logic (tests rely on their presence)
        if count > 0 or (end is not None and end <= 3000):
            histogram.append(HistogramBin(
                start=start,
                end=end,
                count=count,
                percentage=round((count / total * 100), 1) if total > 0 else 0.0,
                label=label
            ))
    return histogram

def get_price_distribution_summary(prices_per_sqm: List[float]) -> Dict:
    if not prices_per_sqm:
        return {"total_ads": 0, "histogram": [], "dominant_range": None, "dominant_percentage": 0.0}
    histogram = build_price_histogram(prices_per_sqm)
    max_bin = max(histogram, key=lambda b: b.count) if histogram else None
    return {
        "total_ads": len(prices_per_sqm),
        "histogram": histogram,
        "dominant_range": max_bin.label if max_bin else None,
        "dominant_percentage": max_bin.percentage if max_bin else 0.0
    }

__all__ = ["build_price_histogram", "get_price_distribution_summary"]
