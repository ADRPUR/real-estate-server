from datetime import datetime
from typing import List, Dict, Optional

from pydantic import BaseModel


class ProimobilListing(BaseModel):
    id: str
    offer: str
    category: str
    status: str
    is_hot: bool
    is_exclusive: bool
    deal: bool
    booked: bool
    order: int
    views: int
    bathrooms: Optional[int] = None
    bedrooms: Optional[int] = None
    balcony: Optional[int] = None
    state: Optional[str] = None
    parking: Optional[str] = None
    price_eur: float
    price_per_sqm: float
    city: str
    city_id: int
    sector: Optional[str] = None
    street: Optional[str] = None
    rooms: Optional[int] = None
    surface_sqm: float
    condition: Optional[str] = None
    floor: Optional[int] = None
    number_of_floors: Optional[int] = None
    updated_at: datetime
    created_at: datetime


class CacheInfo(BaseModel):
    timestamp: datetime
    source: str
    is_stale: bool
    age_seconds: float


class ProimobilListingsResponse(BaseModel):
    total: int
    listings: List[ProimobilListing]
    cache_info: CacheInfo


# --- Analytics models ---

class TimeOnMarketStats(BaseModel):
    avg_days: float
    median_days: float
    p75_days: float
    max_days: int


class ReservationStats(BaseModel):
    total_booked: int
    total_sold: int
    avg_orders_per_listing: float


class EngagementStats(BaseModel):
    avg_views_per_listing: float
    views_per_day_avg: float


class TimeOnMarketByGroup(BaseModel):
    by_sector: Dict[str, TimeOnMarketStats]
    by_state: Dict[str, TimeOnMarketStats]
    by_condition: Dict[str, TimeOnMarketStats]
    by_rooms: Dict[str, TimeOnMarketStats]


class ProimobilAnalytics(BaseModel):
    # general summary
    total_listings: int
    time_on_market: TimeOnMarketStats
    reservations: ReservationStats
    engagement: EngagementStats
    hot_offers_ratio: float
    exclusive_ratio: float

    # detailed analysis
    time_on_market_by_group: TimeOnMarketByGroup
