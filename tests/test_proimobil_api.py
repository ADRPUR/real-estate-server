"""
Tests for proimobil REST API implementation.
"""

from unittest.mock import Mock, patch
from app.scraping.proimobil_api import (
    ProimobilAPIListing,
    fetch_proimobil_api_page,
    _parse_property_from_api_response,
    _extract_surface_from_description,
    _extract_rooms_from_description
)
from app.services.proimobil_api_service import (
    compute_proimobil_api_stats,
    get_detailed_proimobil_api_listings
)


class TestProimobilAPIListing:
    """Test ProimobilAPIListing dataclass."""
    
    def test_listing_creation(self):
        """Test creating a listing instance."""
        listing = ProimobilAPIListing(
            price_eur=88900.0,
            city="Chișinău",
            sector="Râșcani",
            street="Calea Orheiului",
            rooms=2,
            surface_sqm=50.0,
            url_slug="test-slug"
        )
        
        assert listing.price_eur == 88900.0
        assert listing.city == "Chișinău"
        assert listing.rooms == 2
        assert listing.surface_sqm == 50.0
        assert listing.price_per_sqm == 1778.0
    
    def test_listing_price_per_sqm_calculation(self):
        """Test price per sqm is calculated correctly."""
        listing = ProimobilAPIListing(
            price_eur=100000.0,
            city="Test",
            sector="Test",
            street="Test",
            rooms=2,
            surface_sqm=50.0
        )
        
        assert listing.price_per_sqm == 2000.0
    
    def test_listing_zero_surface(self):
        """Test listing with zero surface doesn't crash."""
        listing = ProimobilAPIListing(
            price_eur=100000.0,
            city="Test",
            sector="Test",
            street="Test",
            rooms=2,
            surface_sqm=0.0
        )
        
        assert listing.price_per_sqm == 0.0


class TestHelperFunctions:
    """Test helper extraction functions."""
    
    def test_extract_surface_from_description(self):
        """Test extracting surface area from Romanian text."""
        desc = "Apartament cu suprafața totală de 50 mp"
        surface = _extract_surface_from_description(desc)
        assert surface == 50.0
    
    def test_extract_surface_m2_format(self):
        """Test extracting surface with m2 format."""
        desc = "Apartament 45 m2 în centru"
        surface = _extract_surface_from_description(desc)
        assert surface == 45.0
    
    def test_extract_surface_not_found(self):
        """Test returns None when surface not found."""
        desc = "Apartament frumos în centru"
        surface = _extract_surface_from_description(desc)
        assert surface is None
    
    def test_extract_rooms_from_description(self):
        """Test extracting number of rooms from text."""
        desc = "Apartament cu 2 camere în Râșcani"
        rooms = _extract_rooms_from_description(desc)
        assert rooms == 2
    
    def test_extract_rooms_alternative_format(self):
        """Test extracting rooms with 'camere' format."""
        desc = "Vă propunem 3 camere"
        rooms = _extract_rooms_from_description(desc)
        assert rooms == 3
    
    def test_extract_rooms_not_found(self):
        """Test returns None when rooms not found."""
        desc = "Apartament frumos"
        rooms = _extract_rooms_from_description(desc)
        assert rooms is None


class TestParsePropertyFromAPIResponse:
    """Test parsing property from API response."""
    
    def test_parse_valid_property(self):
        """Test parsing a valid property object."""
        prop = {
            "price": {"amount": 88900, "currency": "€"},
            "i18n": {
                "ro": {
                    "url": "test-url",
                    "address": "Calea Orheiului",
                    "description": "Apartament cu 2 camere, suprafața totală de 50 mp",
                    "characteristics": [
                        {"name": "Suprafața totală", "value": "50 m2"},
                        {"name": "Camere", "value": "2"}
                    ]
                }
            },
            "_embedded": {
                "city": {"i18n": {"ro": {"name": "Chișinău"}}},
                "region": {"i18n": {"ro": {"name": "Râșcani"}}}
            }
        }
        
        listing = _parse_property_from_api_response(prop)
        
        assert listing is not None
        assert listing.price_eur == 88900.0
        assert listing.city == "Chișinău"
        assert listing.sector == "Râșcani"
        assert listing.street == "Calea Orheiului"
        assert listing.rooms == 2
        assert listing.surface_sqm == 50.0
    
    def test_parse_property_missing_price(self):
        """Test returns None if price is missing."""
        prop = {
            "price": {},
            "i18n": {"ro": {}},
            "_embedded": {}
        }
        
        listing = _parse_property_from_api_response(prop)
        assert listing is None
    
    def test_parse_property_missing_surface(self):
        """Test returns None if surface is missing."""
        prop = {
            "price": {"amount": 88900},
            "i18n": {
                "ro": {
                    "description": "Apartament frumos",
                    "characteristics": []
                }
            },
            "_embedded": {
                "city": {"i18n": {"ro": {"name": "Chișinău"}}},
                "region": {"i18n": {"ro": {"name": "Test"}}}
            }
        }
        
        listing = _parse_property_from_api_response(prop)
        assert listing is None


class TestFetchProimobilAPI:
    """Test fetching from proimobil API."""
    
    @patch('app.scraping.proimobil_api.requests.get')
    def test_fetch_api_page_success(self, mock_get):
        """Test successful API fetch."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "price": {"amount": 88900},
                "i18n": {
                    "ro": {
                        "url": "test",
                        "address": "Test St",
                        "description": "2 camere, 50 mp",
                        "characteristics": [
                            {"name": "Suprafața totală", "value": "50 m2"},
                            {"name": "Camere", "value": "2"}
                        ]
                    }
                },
                "_embedded": {
                    "city": {"i18n": {"ro": {"name": "Chișinău"}}},
                    "region": {"i18n": {"ro": {"name": "Test"}}}
                }
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        listings = fetch_proimobil_api_page(offset=0, limit=10)
        
        assert len(listings) == 1
        assert listings[0].price_eur == 88900.0
    
    @patch('app.scraping.proimobil_api.requests.get')
    def test_fetch_api_page_empty_response(self, mock_get):
        """Test API returns empty list."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        listings = fetch_proimobil_api_page(offset=0, limit=10)
        
        assert len(listings) == 0
    
    @patch('app.scraping.proimobil_api.requests.get')
    def test_fetch_api_page_request_error(self, mock_get):
        """Test handles request errors gracefully."""
        mock_get.side_effect = Exception("Connection error")
        
        listings = fetch_proimobil_api_page(offset=0, limit=10)
        
        assert len(listings) == 0


class TestProimobilAPIService:
    """Test proimobil API service functions."""
    
    @patch('app.services.proimobil_api_service.fetch_all_proimobil_api_listings')
    def test_compute_stats_success(self, mock_fetch):
        """Test computing stats from listings."""
        mock_fetch.return_value = [
            ProimobilAPIListing(100000, "Test", "Test", "Test", 2, 50.0),
            ProimobilAPIListing(150000, "Test", "Test", "Test", 3, 75.0),
            ProimobilAPIListing(120000, "Test", "Test", "Test", 2, 60.0),
        ]
        
        stats = compute_proimobil_api_stats(max_items=100)
        
        assert stats.total_ads == 3
        assert stats.min_price_per_sqm == 2000.0
        assert stats.max_price_per_sqm == 2000.0
        assert stats.source == "proimobil_api"
    
    @patch('app.services.proimobil_api_service.fetch_all_proimobil_api_listings')
    def test_compute_stats_empty_listings(self, mock_fetch):
        """Test stats with no listings."""
        mock_fetch.return_value = []
        
        stats = compute_proimobil_api_stats(max_items=100)
        
        assert stats.total_ads == 0
        assert stats.min_price_per_sqm == 0.0
    
    @patch('app.services.proimobil_api_service.fetch_all_proimobil_api_listings')
    def test_get_detailed_listings(self, mock_fetch):
        """Test getting detailed listings."""
        mock_fetch.return_value = [
            ProimobilAPIListing(
                100000, "Chișinău", "Centru", "Test St", 2, 50.0, "test-url"
            )
        ]
        
        listings = get_detailed_proimobil_api_listings(max_items=100)
        
        assert len(listings) == 1
        assert listings[0]["price_eur"] == 100000
        assert listings[0]["city"] == "Chișinău"
        assert "url" in listings[0]

