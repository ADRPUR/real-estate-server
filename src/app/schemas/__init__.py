"""
Pydantic schemas for API request/response models.
"""
from app.schemas.rates import RatesResponse, RatesCacheResponse
from app.schemas.pdf import PDFGenerationRequest, SaleSummaryRequest, PDFResponse
from app.schemas.market import (
    MarketStatsResponse,
    MarketSummaryResponse,
    ListingsResponse,
    ListingItem,
    PriceDistribution,
    PriceDistributionBin,
    QuartilesData,
)

__all__ = [
    # Rates
    "RatesResponse",
    "RatesCacheResponse",
    # PDF
    "PDFGenerationRequest",
    "SaleSummaryRequest",
    "PDFResponse",
    # Market
    "MarketStatsResponse",
    "MarketSummaryResponse",
    "ListingsResponse",
    "ListingItem",
    "PriceDistribution",
    "PriceDistributionBin",
    "QuartilesData",
]

