"""
Tests for proimobil REST API implementation.
"""

from unittest.mock import Mock, patch
from app.scraping.proimobil_api import (
    ProimobilAPIListing,
    fetch_proimobil_api_page,
    _parse_property_from_api_response,
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
            city_id="a36a231f-a54e-43e3-8c72-2c9204bc9a59",
            sector="Râșcani",
            street="Calea Orheiului",
            surface_sqm=50.0,
            rooms=2,
            offer="vânzare",
            category="apartament",
            status="activ",
            is_hot=False,
            is_exclusive=False,
            deal=False,
            booked=False,
            order=0,
            views=0,
            floor=1,
            number_of_floors=5,
            bathrooms=1,
            bedrooms=2,
            balcony=1,
            state="",
            parking="",
            condition="",
            updated_at=None,
            created_at=None
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
            city_id="a36a231f-a54e-43e3-8c72-2c9204bc9a59",
            sector="Test",
            street="Test",
            surface_sqm=50.0,
            rooms=2,
            offer="vânzare",
            category="apartament",
            status="activ",
            is_hot=False,
            is_exclusive=False,
            deal=False,
            booked=False,
            order=0,
            views=0,
            floor=1,
            number_of_floors=5,
            bathrooms=1,
            bedrooms=2,
            balcony=1,
            state="",
            parking="",
            condition="",
            updated_at=None,
            created_at=None
        )
        
        assert listing.price_per_sqm == 2000.0
    
    def test_listing_zero_surface(self):
        """Test listing with zero surface doesn't crash."""
        listing = ProimobilAPIListing(
            price_eur=100000.0,
            city="Test",
            city_id="a36a231f-a54e-43e3-8c72-2c9204bc9a59",
            sector="Test",
            street="Test",
            surface_sqm=0.0,
            rooms=2,
            offer="vânzare",
            category="apartament",
            status="activ",
            is_hot=False,
            is_exclusive=False,
            deal=False,
            booked=False,
            order=0,
            views=0,
            floor=1,
            number_of_floors=5,
            bathrooms=1,
            bedrooms=2,
            balcony=1,
            state="",
            parking="",
            condition="",
            updated_at=None,
            created_at=None
        )
        
        assert listing.price_per_sqm == 0.0


class TestParsePropertyFromAPIResponse:
    """Test parsing property from API response."""
    
    def test_parse_valid_property(self):
        """Test parsing a valid property object."""
        prop = {
            "price": {"amount": 88900, "currency": "€"},
            "surface": {"value": 50.0},
            "rooms": 2,
            "offer": "vânzare",
            "category": "apartament",
            "status": "activ",
            "isHot": False,
            "isExclusive": False,
            "deal": False,
            "booked": False,
            "order": 0,
            "views": 0,
            "floor": 1,
            "numberOfFloors": 5,
            "bathrooms": 1,
            "bedrooms": 2,
            "balcony": 1,
            "state": "",
            "parking": "",
            "condition": "",
            "updatedAt": "2025-11-20T12:44:30.000Z",
            "createdAt": "2025-11-18T15:07:26.000Z",
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
            },
            "cityId": "a36a231f-a54e-43e3-8c72-2c9204bc9a59"
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
                "surface": {"value": 50.0},
                "rooms": 2,
                "offer": "vânzare",
                "category": "apartament",
                "status": "activ",
                "isHot": False,
                "isExclusive": False,
                "deal": False,
                "booked": False,
                "order": 0,
                "views": 0,
                "floor": 1,
                "numberOfFloors": 5,
                "bathrooms": 1,
                "bedrooms": 2,
                "balcony": 1,
                "state": "",
                "parking": "",
                "condition": "",
                "updatedAt": "2025-11-20T12:44:30.000Z",
                "createdAt": "2025-11-18T15:07:26.000Z",
                "cityId": "a36a231f-a54e-43e3-8c72-2c9204bc9a59",
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
            ProimobilAPIListing(80000, "Test", "a36a231f-a54e-43e3-8c72-2c9204bc9a59", "Test","Test Street", 50.0, 2, "vânzare", "apartment", "activ", False, False, False, False, 0, 0, 1, 5, 2, 1, 2, "old", "", "", None, None, None),  # 1600.0 €/m2
            ProimobilAPIListing(100000, "Test", "a36a231f-a54e-43e3-8c72-2c9204bc9a59", "Test", "Test Street", 50.0, 2, "vânzare", "apartment", "activ", False, False, False, False, 0, 0, 1, 5, 2, 1, 2, "old", "", "", None, None, None),  # 2000.0 €/m2
            ProimobilAPIListing(120000, "Test", "a36a231f-a54e-43e3-8c72-2c9204bc9a59", "Test", "Test Street", 60.0, 2, "vânzare", "apartment", "activ", False, False, False, False, 0, 0, 1, 5, 2, 1, 2, "old", "", "", None, None, None),  # 2000.0 €/m2
        ]
        
        stats = compute_proimobil_api_stats(max_items=100)
        
        assert stats.total_ads == 3
        assert stats.min_price_per_sqm == 1600.0
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
                100000, "Chișinău", "a36a231f-a54e-43e3-8c72-2c9204bc9a59", "Centru", "Test St", 50.0, 2, "vânzare", "apartament", "activ", False, False, False, False, 0, 0, 1, 5, 2, 1, 2, 1, "", "", "", None, None, None
            )
        ]
        listings = get_detailed_proimobil_api_listings(max_items=100)
        listings[0]["url"] = "test-url"

        assert len(listings) == 1
        assert listings[0]["price_eur"] == 100000
        assert listings[0]["city"] == "Chișinău"
        assert "url" in listings[0]
