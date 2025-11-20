"""
Direct REST API calls to proimobil.md - clean JSON response, no scraping needed.
Uses the official proimobil.md API endpoint: https://api.proimobil.md/v1/properties
"""

import logging
import re
from typing import List, Dict, Any, Optional
import requests
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ProimobilAPIListing:
    """Represents a single property listing from proimobil REST API."""
    
    def __init__(
        self,
        price_eur: float,
        city: str,
        sector: str,
        street: str,
        rooms: int,
        surface_sqm: float,
        url_slug: Optional[str] = None
    ):
        self.price_eur = price_eur
        self.city = city
        self.sector = sector
        self.street = street
        self.rooms = rooms
        self.surface_sqm = surface_sqm
        self.url_slug = url_slug
        self.price_per_sqm = price_eur / surface_sqm if surface_sqm > 0 else 0.0
    
    def __repr__(self):
        return (f"ProimobilAPIListing(price={self.price_eur}€, "
                f"city={self.city}, sector={self.sector}, street={self.street}, "
                f"rooms={self.rooms}, surface={self.surface_sqm}m², "
                f"€/m²={self.price_per_sqm:.2f})")


def _extract_surface_from_description(description: str) -> Optional[float]:
    """
    Extract surface area from Romanian description text.
    Looks for patterns like "50 mp", "50 m2", "50mp", etc.
    """
    if not description:
        return None
    
    # Try to find "suprafața totală de X mp" or "suprafața totală de X m2"
    patterns = [
        r'suprafața\s+totală\s+de\s+(\d+(?:[.,]\d+)?)\s*(?:mp|m2|m²)',
        r'suprafata\s+totala\s+de\s+(\d+(?:[.,]\d+)?)\s*(?:mp|m2|m²)',
        r'(\d+(?:[.,]\d+)?)\s*(?:mp|m2|m²)',  # Generic pattern as fallback
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            surface_str = match.group(1).replace(',', '.')
            try:
                return float(surface_str)
            except ValueError:
                continue
    
    return None


def _extract_rooms_from_description(description: str) -> Optional[int]:
    """
    Extract number of rooms from Romanian description text.
    Looks for patterns like "2 camere", "cu 2 camere", etc.
    """
    if not description:
        return None
    
    patterns = [
        r'(?:cu\s+)?(\d+)\s+(?:camere|camera)',
        r'apartament\s+cu\s+(\d+)\s+(?:camere|camera)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    
    return None


def _parse_property_from_api_response(prop: Dict[str, Any]) -> Optional[ProimobilAPIListing]:
    """
    Parse a single property object from the proimobil REST API response.
    
    Args:
        prop: Property dictionary from API response
    
    Returns:
        ProimobilAPIListing object or None if required data is missing
    """
    try:
        # Extract price
        price_obj = prop.get("price", {})
        price_eur = price_obj.get("amount")
        if not price_eur:
            return None
        
        # Extract i18n data (Romanian language)
        i18n_ro = prop.get("i18n", {}).get("ro", {})
        description = i18n_ro.get("description", "")
        street = i18n_ro.get("address", "")
        url_slug = i18n_ro.get("url", "")
        
        # Extract surface from characteristics or description
        characteristics = i18n_ro.get("characteristics", [])
        surface_sqm = None
        rooms = None
        
        for char in characteristics:
            name = char.get("name", "")
            value = char.get("value", "")
            
            if "Suprafața totală" in name or "Suprafata totala" in name:
                # Extract number from "50 m2" or "50 mp"
                match = re.search(r'(\d+(?:[.,]\d+)?)', value)
                if match:
                    surface_sqm = float(match.group(1).replace(',', '.'))
            
            elif "Camere" in name:
                # Extract number of rooms
                match = re.search(r'(\d+)', value)
                if match:
                    rooms = int(match.group(1))
        
        # Fallback: extract from description if not in characteristics
        if surface_sqm is None:
            surface_sqm = _extract_surface_from_description(description)
        
        if rooms is None:
            rooms = _extract_rooms_from_description(description)
        
        # Check if we have minimum required data
        if surface_sqm is None or surface_sqm == 0:
            return None
        
        # Extract city and region from _embedded
        embedded = prop.get("_embedded", {})
        city_obj = embedded.get("city", {})
        region_obj = embedded.get("region", {})
        
        city = city_obj.get("i18n", {}).get("ro", {}).get("name", "")
        sector = region_obj.get("i18n", {}).get("ro", {}).get("name", "")
        
        return ProimobilAPIListing(
            price_eur=float(price_eur),
            city=city,
            sector=sector,
            street=street,
            rooms=rooms if rooms else 0,
            surface_sqm=surface_sqm,
            url_slug=url_slug
        )
        
    except Exception as e:
        logger.debug(f"Failed to parse property: {e}")
        return None


def _extract_listings_from_api_response(data: List[Dict[str, Any]]) -> List[ProimobilAPIListing]:
    """
    Extract all valid listings from API response array.
    
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


def fetch_all_proimobil_api_listings(max_items: int = 500) -> List[ProimobilAPIListing]:
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
    
    logger.info(f"Total listings fetched from proimobil API: {len(all_listings)}")
    return all_listings


def get_proimobil_api_prices(max_items: int = 500) -> List[float]:
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

