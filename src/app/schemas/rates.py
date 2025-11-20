"""
Pydantic schemas for rates endpoints.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field


class RatesResponse(BaseModel):
    """Response model for /rates endpoint."""

    eur_to_mdl: Optional[float] = Field(None, description="EUR to MDL exchange rate")
    usd_to_mdl: Optional[float] = Field(None, description="USD to MDL exchange rate")
    eur_to_ron: Optional[float] = Field(None, description="EUR to RON exchange rate")
    usd_to_ron: Optional[float] = Field(None, description="USD to RON exchange rate")
    ron_to_mdl: Optional[float] = Field(None, description="RON to MDL exchange rate")
    timestamp: Optional[str] = Field(None, description="Timestamp of rates fetch")

    class Config:
        json_schema_extra = {
            "example": {
                "eur_to_mdl": 19.5,
                "usd_to_mdl": 17.8,
                "eur_to_ron": 4.97,
                "usd_to_ron": 4.55,
                "ron_to_mdl": 3.92,
                "timestamp": "2025-11-20T10:00:00Z"
            }
        }


class RatesCacheResponse(BaseModel):
    """Response model for rates with cache info."""

    rates: RatesResponse
    cached: bool = Field(..., description="Whether rates were served from cache")
    cache_age_seconds: Optional[float] = Field(None, description="Age of cached data in seconds")

