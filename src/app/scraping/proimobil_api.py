"""
Direct REST API calls to proimobil.md - clean JSON response, no scraping needed.
Uses the official proimobil.md API endpoint: https://api.proimobil.md/v1/properties
"""

import logging
from typing import List, Dict, Any, Optional
import requests
import urllib3
from datetime import datetime

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ProimobilAPIListing:
    """Represents a single property listing from proimobil REST API."""
    
    def __init__(
        self,
        price_eur: float,
        city: str,
        city_id: str,
        sector: str,
        street: str,
        surface_sqm: float,
        rooms: int,
        offer: str,
        category: str,
        status: str,
        is_hot: bool,
        is_exclusive: bool,
        deal: bool,
        booked: bool,
        order: int,
        views: int,
        floor: int,
        number_of_floors: int,
        bathrooms: int,
        bedrooms: int,
        balcony: int,
        state: str,
        parking: str,
        condition: str,
        updated_at: Optional[datetime],
        created_at: Optional[datetime],
        listing_id: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.price_eur = price_eur
        self.city = city
        self.city_id = city_id
        self.sector = sector
        self.street = street
        self.rooms = rooms
        self.surface_sqm = surface_sqm
        self.price_per_sqm = price_eur / surface_sqm if surface_sqm > 0 else 0.0
        self.listing_id = listing_id
        self.offer = offer
        self.category = category
        self.status = status
        self.is_hot = is_hot
        self.is_exclusive = is_exclusive
        self.deal = deal
        self.booked = booked
        self.order = order
        self.views = views
        self.floor = floor
        self.number_of_floors = number_of_floors
        self.bathrooms = bathrooms
        self.bedrooms = bedrooms
        self.balcony = balcony
        self.state = state
        self.parking = parking
        self.condition = condition
        self.updated_at = updated_at
        self.created_at = created_at
        self.url = url

    def __repr__(self):
        return (f"ProimobilAPIListing(price={self.price_eur}€, "
                f"city={self.city}, sector={self.sector}, street={self.street}, "
                f"rooms={self.rooms}, surface={self.surface_sqm}m², "
                f"€/m²={self.price_per_sqm:.2f})")


def _parse_property_from_api_response(prop: Dict[str, Any]) -> Optional[ProimobilAPIListing]:
    """
    Parse a single property object from the proimobil REST API response.
    
    Args:
        prop: Property dictionary from API response
    
    Returns:
        ProimobilAPIListing object (nu mai returnează None, pune valori default)
    """
    try:
        # Extract listing ID
        listing_id = prop.get("id", "")

        # Extract city ID (poate lipsi)
        city_id = prop.get("cityId", "")

        # Extract price
        price_obj = prop.get("price", {})
        price_eur = price_obj.get("amount", 0.0)

        # Extract i18n data (Romanian language)
        i18n_ro = prop.get("i18n", {}).get("ro", {})
        street = i18n_ro.get("address", "")

        # Extract surface
        surface_obj = prop.get("surface", {})
        surface_sqm = surface_obj.get("value", 0.0)

        # Extract rooms
        rooms = prop.get("rooms", 0)

        # Extract offer
        offer = prop.get("offer", "")

        # Extract category
        category = prop.get("category", "")

        # Extract status
        status = prop.get("status", "")

        # Extract other fields with defaults
        is_hot = prop.get("isHot", False)
        is_exclusive = prop.get("isExclusive", False)
        deal = prop.get("deal", False)
        booked = prop.get("booked", False)
        order = prop.get("order", 0)
        views = prop.get("views", 0)
        floor = prop.get("floor", 0)
        number_of_floors = prop.get("numberOfFloors", 0)
        bathrooms = prop.get("bathrooms", 0)
        bedrooms = prop.get("bedrooms", 0)
        balcony = prop.get("balcony", 0)
        state = prop.get("state", "")
        parking = prop.get("parking", "")
        condition = prop.get("condition", "")
        updated_at_str = prop.get("updatedAt", "")
        created_at_str = prop.get("createdAt", "")
        updated_at = None
        created_at = None
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except Exception:
                updated_at = None
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except Exception:
                created_at = None

        # Extract city and region from _embedded
        embedded = prop.get("_embedded", {})
        city_obj = embedded.get("city", {})
        region_obj = embedded.get("region", {})
        city = city_obj.get("i18n", {}).get("ro", {}).get("name", "")
        sector = region_obj.get("i18n", {}).get("ro", {}).get("name", "")

        return ProimobilAPIListing(
            price_eur=float(price_eur) if price_eur else 0.0,
            city=city,
            city_id=city_id,
            sector=sector,
            street=street,
            rooms=rooms if rooms else 0,
            surface_sqm=surface_sqm if surface_sqm else 0.0,
            offer=offer,
            category=category,
            status=status,
            is_hot=is_hot,
            is_exclusive=is_exclusive,
            deal=deal,
            booked=booked,
            order=order,
            views=views,
            floor=floor,
            number_of_floors=number_of_floors,
            bathrooms=bathrooms,
            bedrooms=bedrooms,
            balcony=balcony,
            state=state,
            parking=parking,
            condition=condition,
            updated_at=updated_at,
            created_at=created_at,
            listing_id=str(listing_id) if listing_id else None
        )
    except Exception as e:
        logger.debug(f"Failed to parse property: {e}")
        return None


def _extract_listings_from_api_response(data: List[Dict[str, Any]]) -> List[ProimobilAPIListing]:
    """
    Extract all valid listings from API response array, filtrand doar cele din Chisinau (cityId specificat).

    Args:
        data: Array of property objects from API
    
    Returns:
        List of ProimobilAPIListing objects
    """
    listings = []
    
    for prop in data:
        listing = _parse_property_from_api_response(prop)
        if listing:
            listings.append(listing)
    
    return listings


def fetch_proimobil_api_page(offset: int = 0, limit: int = 150) -> List[ProimobilAPIListing]:
    """
    Fetch listings from proimobil.md REST API.
    
    Args:
        offset: Offset for pagination (0-based)
        limit: Number of items to fetch (max 150)
    
    Returns:
        List of ProimobilAPIListing objects
    """
    # Official REST API endpoint
    base_url = "https://api.proimobil.md/v1/properties"
    
    # Build query parameters
    params = {
        "filter": "status:active",  # Only active listings
        "sort": "-isHot,-isExclusive,-surrogateId",  # Sort by hot first
        "limit": min(limit, 150),  # Max 150 per request
        "offset": offset,
        "embedded": "agents,city,region"  # Include related data
    }
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "ro,en-US;q=0.9,en;q=0.8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        logger.info(f"Fetching proimobil API: offset={offset}, limit={limit}")
        resp = requests.get(base_url, params=params, headers=headers, timeout=15, verify=False)
        resp.raise_for_status()
        
        # Parse JSON response
        data = resp.json()
        
        # The response should be an array of property objects
        if not isinstance(data, list):
            logger.error(f"Unexpected API response format: {type(data)}")
            return []
        
        # Extract listings
        listings = _extract_listings_from_api_response(data)
        
        logger.info(f"Extracted {len(listings)} listings from proimobil API (offset={offset})")
        return listings
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch proimobil API: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing proimobil API response: {e}", exc_info=True)
        return []


def fetch_all_proimobil_api_listings(max_items: int = 1000) -> List[ProimobilAPIListing]:
    """
    Fetch all available listings from proimobil.md API.
    
    Args:
        max_items: Maximum number of items to fetch total
    
    Returns:
        List of all ProimobilAPIListing objects
    """
    all_listings = []
    offset = 0
    batch_size = 150  # API maximum

    
    while offset < max_items:
        # Fetch one batch
        listings = fetch_proimobil_api_page(offset=offset, limit=batch_size)
        
        if not listings:
            logger.info(f"No more listings found at offset {offset}, stopping pagination")
            break
        
        all_listings.extend(listings)
        
        # If we got fewer than requested, we've reached the end
        if len(listings) < batch_size:
            logger.info(f"Got {len(listings)} < {batch_size}, reached end of listings")
            break
        
        offset += batch_size

    # Filtrare doar anunțuri din Chișinău și cu offer = 'sell'
    chisinau_city_id = "a36a231f-a54e-43e3-8c72-2c9204bc9a59"
    all_listings = [listing for listing in all_listings if (getattr(listing, 'cityId', None) == chisinau_city_id or getattr(listing, 'city_id', None) == chisinau_city_id) and getattr(listing, 'offer', None) == 'sell']
    logger.info(f"Total listings fetched from proimobil API: {len(all_listings)}")
    return all_listings


def get_proimobil_api_prices(max_items: int = 1000) -> List[float]:
    """
    Get all price-per-sqm values from proimobil API.
    
    Args:
        max_items: Maximum number of items to fetch
    
    Returns:
        List of prices per square meter
    """
    listings = fetch_all_proimobil_api_listings(max_items)
    prices = [listing.price_per_sqm for listing in listings if listing.price_per_sqm > 0]
    return prices
