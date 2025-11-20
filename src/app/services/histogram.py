from dataclasses import dataclass
from typing import List, Optional, Iterable

@dataclass
class HistogramBin:
    start: float
    end: Optional[float]
    count: int
    percentage: float
    label: str

PRICE_INTERVALS = [
    (0, 1100, "<1100"),
    (1100, 1500, "1100-1500"),
    (1500, 1800, "1500-1800"),
    (1800, 2200, "1800-2200"),
    (2200, 2600, "2200-2600"),
    (2600, 3000, "2600-3000"),
    (3000, 3500, "3000-3500"),
    (3500, None, ">3500"),
]

def build_price_histogram(prices: Iterable[float]) -> List[HistogramBin]:
    prices_list = list(p for p in prices if p is not None)
    if not prices_list:
        return []
    total = len(prices_list)
    bins: List[HistogramBin] = []
    for start, end, label in PRICE_INTERVALS:
        if end is None:
            count = sum(1 for p in prices_list if p >= start)
        else:
            count = sum(1 for p in prices_list if start <= p < end)
        percentage = round((count / total) * 100, 1) if total else 0.0
        bins.append(HistogramBin(start=start, end=end, count=count, percentage=percentage, label=label))
    return bins

def get_price_distribution_summary(prices: Iterable[float]) -> dict:
    prices_list = list(prices)
    bins = build_price_histogram(prices_list)
    if not bins:
        return {"total_ads": 0, "histogram": [], "dominant_range": None, "dominant_percentage": 0.0}
    dominant = max(bins, key=lambda b: b.count)
    return {
        "total_ads": len(prices_list),
        "histogram": [
            {"start": b.start, "end": b.end, "count": b.count, "percentage": b.percentage, "label": b.label}
            for b in bins
        ],
        "dominant_range": dominant.label,
        "dominant_percentage": dominant.percentage,
    }
