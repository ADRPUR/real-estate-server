from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HistogramBin:
    start: float
    end: Optional[float]
    count: int
    percentage: float = 0.0
    label: str = ""

@dataclass
class MarketStats:
    source: str
    url: Optional[str]
    total_ads: int
    min_price_per_sqm: float
    max_price_per_sqm: float
    avg_price_per_sqm: float
    median_price_per_sqm: float
    price_histogram: Optional[List[HistogramBin]] = None
    dominant_range: Optional[str] = None
    dominant_percentage: Optional[float] = None
    # Quartile analysis
    q1_price_per_sqm: Optional[float] = None  # 25th percentile - preț minim realist
    q2_price_per_sqm: Optional[float] = None  # 50th percentile - median (duplicate for clarity)
    q3_price_per_sqm: Optional[float] = None  # 75th percentile - zona premium
    iqr_price_per_sqm: Optional[float] = None  # Interquartile Range (Q3 - Q1)

