"""
Pydantic schemas for market data endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PriceDistributionBin(BaseModel):
    """Single bin in price distribution histogram."""

    range: str = Field(..., description="Price range (e.g., '1000-1500')")
    count: int = Field(..., description="Number of listings in this range")
    percentage: float = Field(..., description="Percentage of total listings")


class PriceDistribution(BaseModel):
    """Price distribution histogram data."""

    bins: List[PriceDistributionBin] = Field(..., description="Distribution bins")
    dominant_range: Optional[str] = Field(None, description="Most common price range")
    dominant_percentage: Optional[float] = Field(None, description="Percentage in dominant range")


class QuartilesData(BaseModel):
    """Quartile analysis data."""

    q1: float = Field(..., description="First quartile (25th percentile)")
    q2: float = Field(..., description="Second quartile (median, 50th percentile)")
    q3: float = Field(..., description="Third quartile (75th percentile)")
    iqr: float = Field(..., description="Interquartile range (Q3 - Q1)")
    market_width: str = Field(..., description="Market width category (narrow/moderate/wide)")
    q1_percentage: float = Field(..., description="Percentage of listings below Q1")
    q2_percentage: float = Field(..., description="Percentage of listings below Q2")
    q3_percentage: float = Field(..., description="Percentage of listings below Q3")


class MarketStatsResponse(BaseModel):
    """Response model for market statistics."""

    source: str = Field(..., description="Data source (proimobil, accesimobil, 999md)")
    total_ads: int = Field(..., description="Total number of ads analyzed")
    avg_price_per_sqm: Optional[float] = Field(None, description="Average price per sqm")
    median_price_per_sqm: Optional[float] = Field(None, description="Median price per sqm")
    min_price_per_sqm: Optional[float] = Field(None, description="Minimum price per sqm")
    max_price_per_sqm: Optional[float] = Field(None, description="Maximum price per sqm")
    std_dev: Optional[float] = Field(None, description="Standard deviation")
    currency: str = Field("EUR", description="Currency of prices")
    quartiles: Optional[QuartilesData] = Field(None, description="Quartile analysis")
    distribution: Optional[PriceDistribution] = Field(None, description="Price distribution")
    timestamp: Optional[str] = Field(None, description="Data fetch timestamp")
    cached: bool = Field(False, description="Whether data was served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "proimobil",
                "total_ads": 450,
                "avg_price_per_sqm": 1850.5,
                "median_price_per_sqm": 1750.0,
                "min_price_per_sqm": 800.0,
                "max_price_per_sqm": 3500.0,
                "std_dev": 450.2,
                "currency": "EUR",
                "cached": True,
                "timestamp": "2025-11-20T10:00:00Z"
            }
        }


class MarketSummaryResponse(BaseModel):
    """Response model for aggregated market summary."""

    proimobil: Optional[MarketStatsResponse] = Field(None, description="Proimobil statistics")
    accesimobil: Optional[MarketStatsResponse] = Field(None, description="Accesimobil statistics")
    md999: Optional[MarketStatsResponse] = Field(None, description="999.md statistics")
    aggregate: Optional[Dict[str, Any]] = Field(None, description="Aggregated statistics across all sources")
    timestamp: str = Field(..., description="Summary generation timestamp")


class ListingItem(BaseModel):
    """Single real estate listing."""

    price: float = Field(..., description="Listing price")
    surface: float = Field(..., description="Surface area in sqm")
    price_per_sqm: float = Field(..., description="Price per square meter")
    url: Optional[str] = Field(None, description="Listing URL")
    location: Optional[str] = Field(None, description="Property location")
    rooms: Optional[int] = Field(None, description="Number of rooms")
    updated_at: Optional[str] = Field(None, description="Last update date (ISO 8601)")
    created_at: Optional[str] = Field(None, description="Creation date (ISO 8601)")


class ListingsResponse(BaseModel):
    """Response model for listings list."""

    source: str = Field(..., description="Data source")
    total: int = Field(..., description="Total number of listings")
    listings: List[ListingItem] = Field(..., description="List of listings")
    cached: bool = Field(False, description="Whether data was served from cache")
