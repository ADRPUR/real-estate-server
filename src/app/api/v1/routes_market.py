from fastapi import APIRouter, Query, HTTPException
from app.core.config import get_settings
from app.scraping.proimobil import compute_proimobil_stats
from app.scraping.accesimobil import compute_stats_for_accesimobil
from app.scraping.md999 import compute_999md_stats, fetch_all_999md_prices
from app.services.histogram import get_price_distribution_summary
from app.scraping.proimobil import fetch_all_proimobil_prices
from app.scraping.accesimobil import fetch_all_prices_accesimobil
from app.services.quartile_analysis import (
    calculate_quartiles,
    remove_outliers_iqr
)
from app.services.proimobil_api_service import (
    compute_proimobil_api_stats,
    get_detailed_proimobil_api_listings
)
from app.services.market_analytics import (
    analyze_market,
    score_property,
    get_price_predictions,
    find_similar_properties
)
from typing import Optional
from dataclasses import asdict

router = APIRouter(prefix='/market', tags=['market'])
settings = get_settings()

@router.get('/proimobil')
async def proimobil():
    return compute_proimobil_stats(settings.proimobil_url)

@router.get('/accesimobil')
async def accesimobil():
    """
    Get market stats from accesimobil.md.

    Data is cached and refreshed automatically every 30 minutes (configurable).
    """
    from dataclasses import asdict
    from app.services.cache import get_market_cache

    cache = get_market_cache()

    # Try to get from cache
    cached_data = cache.get('accesimobil')
    if cached_data:
        return cached_data

    # Cache miss - fetch fresh data
    stats = compute_stats_for_accesimobil(settings.accesimobil_url)
    result = asdict(stats)

    # Store in cache
    cache.set('accesimobil', result, source='api_request')

    return result

@router.get('/999md')
async def md999():
    """Get market stats from 999.md (uses Selenium for dynamic content)."""
    from dataclasses import asdict

    # Check if Selenium is available
    selenium_ok = False
    try:
        import selenium
        from webdriver_manager.chrome import ChromeDriverManager
        selenium_ok = True
    except ImportError:
        pass

    if not settings.enable_999md_scraper:
        return {
            "source": "999.md",
            "enabled": False,
            "selenium_installed": selenium_ok,
            "message": "999.md scraper disabled via settings. Set APP_ENABLE_999MD_SCRAPER=True to enable.",
            "total_ads": 0,
            "min_price_per_sqm": 0.0,
            "max_price_per_sqm": 0.0,
            "avg_price_per_sqm": 0.0,
            "median_price_per_sqm": 0.0,
        }

    if not selenium_ok:
        return {
            "source": "999.md",
            "enabled": True,
            "selenium_installed": False,
            "message": "Selenium not installed. Run: pip install selenium webdriver-manager",
            "total_ads": 0,
            "min_price_per_sqm": 0.0,
            "max_price_per_sqm": 0.0,
            "avg_price_per_sqm": 0.0,
            "median_price_per_sqm": 0.0,
        }

    from app.services.cache import get_market_cache

    cache = get_market_cache()

    # Try to get from cache
    cached_data = cache.get('999md')
    if cached_data:
        return cached_data

    # Cache miss - fetch fresh data
    stats = await compute_999md_stats(settings.md999_url)
    data = asdict(stats)
    data["enabled"] = True
    data["selenium_installed"] = True

    # Store in cache
    cache.set('999md', data, source='api_request')

    return data

@router.get('/distribution')
async def distribution():
    """Get price distribution from all sources (proimobil + accesimobil + 999.md)."""
    # Fetch prices from all sources
    prices_pro = fetch_all_proimobil_prices(settings.proimobil_url)
    prices_acc = fetch_all_prices_accesimobil(settings.accesimobil_url)
    prices_999 = await fetch_all_999md_prices(settings.md999_url)

    # Combine all prices
    all_prices = prices_pro + prices_acc + prices_999

    return get_price_distribution_summary(all_prices)


@router.get('/quartiles')
async def quartiles():
    """
    Get quartile analysis from all sources.

    Returns Q1, Q2 (median), Q3, and IQR for price distribution.
    Useful for identifying realistic price ranges and eliminating outliers.

    Response includes:
    - q1: 25th percentile (realistic minimum price)
    - q2: 50th percentile (median)
    - q3: 75th percentile (premium zone)
    - iqr: Interquartile Range (Q3 - Q1) - market width
    - total_ads: Number of ads analyzed
    - outliers_removed: Number of extreme outliers detected (using IQR method)
    - interpretation: Human-readable description of market distribution
    """
    # Fetch prices from all sources
    prices_pro = fetch_all_proimobil_prices(settings.proimobil_url)
    prices_acc = fetch_all_prices_accesimobil(settings.accesimobil_url)
    prices_999 = await fetch_all_999md_prices(settings.md999_url)

    # Combine all prices
    all_prices = prices_pro + prices_acc + prices_999

    if not all_prices:
        return {
            "error": "No prices available",
            "q1": 0.0,
            "q2": 0.0,
            "q3": 0.0,
            "iqr": 0.0,
            "total_ads": 0,
            "outliers_removed": 0
        }

    # Calculate quartiles
    quartiles_data = calculate_quartiles(all_prices)

    # Detect and count outliers
    filtered_prices, num_outliers = remove_outliers_iqr(all_prices)

    # Interpretation (in English)
    q1 = quartiles_data['q1']
    q3 = quartiles_data['q3']
    iqr = quartiles_data['iqr']

    interpretation = {
        "market_width": "narrow" if iqr < 300 else "moderate" if iqr < 600 else "wide",
        "price_range_description": f"Most prices are between {q1:.0f} €/m² (Q1) and {q3:.0f} €/m² (Q3)",
        "iqr_description": f"The central price distribution has a width of {iqr:.0f} €/m²",
        "budget_range": f"< {q1:.0f} €/m²",
        "affordable_range": f"{q1:.0f} - {quartiles_data['q2']:.0f} €/m²",
        "mid_range": f"{quartiles_data['q2']:.0f} - {q3:.0f} €/m²",
        "premium_range": f"> {q3:.0f} €/m²",
    }

    return {
        **quartiles_data,
        "total_ads": len(all_prices),
        "outliers_removed": num_outliers,
        "outliers_percentage": round((num_outliers / len(all_prices)) * 100, 2) if all_prices else 0,
        "interpretation": interpretation,
        "sources": {
            "proimobil": len(prices_pro),
            "accesimobil": len(prices_acc),
            "999md": len(prices_999)
        }
    }


@router.get('/proimobil-api')
async def proimobil_api():
    """
    Get market stats from proimobil.md using direct API calls (no scraping).

    This endpoint uses proimobil's internal REST API instead of scraping HTML.
    Benefits:
    - Much faster than HTML scraping
    - More reliable (no HTML structure changes)
    - Gets all data including rooms, surface, full address

    Data is cached and refreshed automatically every 30 minutes (configurable).
    """
    from dataclasses import asdict
    from app.services.cache import get_market_cache

    cache = get_market_cache()

    # Try to get from cache
    cached_data = cache.get('proimobil_api')
    if cached_data:
        return cached_data

    # Cache miss - fetch fresh data
    stats = compute_proimobil_api_stats()
    result = asdict(stats)

    # Store in cache
    cache.set('proimobil_api', result, source='api_request')

    return result


@router.get('/proimobil-api/listings')
async def proimobil_api_listings():
    """
    Get detailed listings from proimobil.md API.

    Returns full information for each property including:
    - Price (EUR and per m²)
    - Address (city, sector, street)
    - Rooms
    - Surface area
    - URL

    Data is cached and refreshed automatically every 30 minutes (configurable).
    """
    from app.services.cache import get_market_cache

    cache = get_market_cache()

    # Try to get from cache
    cached_data = cache.get('proimobil_api_listings')
    if cached_data:
        return cached_data

    # Cache miss - fetch fresh data
    listings = get_detailed_proimobil_api_listings()
    result = {
        "total": len(listings),
        "listings": listings
    }

    # Store in cache
    cache.set('proimobil_api_listings', result, source='api_request')

    return result


@router.get('/analytics/insights')
async def market_insights():
    """
    Get comprehensive market analytics and insights.

    Provides:
    - Sector analysis (top sectors by volume and price)
    - Price distribution and ranges
    - Room distribution statistics
    - Underpriced/overpriced property counts
    - Premium vs budget sectors
    - Best value sectors for investment
    - Emerging areas

    Based on detailed proimobil API data.
    """
    from app.services.cache import get_market_cache

    cache = get_market_cache()

    # Check cache first
    cached_insights = cache.get('market_insights')
    if cached_insights:
        return cached_insights

    # Get listings
    listings = get_detailed_proimobil_api_listings()

    if not listings:
        raise HTTPException(status_code=404, detail="No listings available for analysis")

    # Analyze market
    insights = analyze_market(listings)
    result = asdict(insights)

    # Cache for 30 minutes
    cache.set('market_insights', result, source='api_request')

    return result


@router.get('/analytics/property-score/{listing_id}')
async def property_score(listing_id: str):
    """
    Get investment and value score for a specific property.

    Returns:
    - Price score (0-100): How competitive is the price
    - Location score (0-100): How desirable is the location
    - Size score (0-100): How optimal is the size for room count
    - Overall score (0-100): Combined investment score
    - Value assessment: "excellent", "good", "fair", or "poor"
    - Predicted price range
    - Market comparison percentage

    Args:
        listing_id: Property ID (url_slug) from proimobil API
    """
    # Get listings and insights
    listings = get_detailed_proimobil_api_listings()

    # Find the specific listing
    target_listing = None
    for listing in listings:
        if listing.get('url_slug') == listing_id or listing.get('id') == listing_id:
            target_listing = listing
            break

    if not target_listing:
        raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")

    # Get or compute market insights
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    cached_insights = cache.get('market_insights')
    if cached_insights:
        # Reconstruct MarketInsights from dict
        from app.services.market_analytics import MarketInsights
        insights = MarketInsights(**cached_insights)
    else:
        insights = analyze_market(listings)
        cache.set('market_insights', asdict(insights), source='api_request')

    # Score the property
    score = score_property(target_listing, insights)

    return {
        **asdict(score),
        'listing_details': {
            'price_eur': target_listing['price_eur'],
            'price_per_sqm': target_listing['price_per_sqm'],
            'surface_sqm': target_listing['surface_sqm'],
            'rooms': target_listing.get('rooms'),
            'sector': target_listing.get('sector'),
            'street': target_listing.get('street')
        }
    }


@router.get('/analytics/predict-price')
async def predict_price(
    surface: float = Query(..., description="Surface area in square meters", gt=0),
    rooms: int = Query(..., description="Number of rooms", ge=1, le=10),
    sector: Optional[str] = Query(None, description="Sector/neighborhood (optional)")
):
    """
    Predict property price based on characteristics.

    Uses machine learning-like statistical analysis to predict:
    - Expected price in EUR
    - Expected price per sqm
    - Confidence interval (min-max range)
    - Market comparison

    Args:
        surface: Surface area in sqm (required)
        rooms: Number of rooms (required)
        sector: Sector/neighborhood name (optional)

    Example:
        /analytics/predict-price?surface=55&rooms=2&sector=Botanica
    """
    # Get market insights
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    cached_insights = cache.get('market_insights')
    if cached_insights:
        from app.services.market_analytics import MarketInsights
        insights = MarketInsights(**cached_insights)
    else:
        listings = get_detailed_proimobil_api_listings()
        insights = analyze_market(listings)
        cache.set('market_insights', asdict(insights), source='api_request')

    # Get prediction
    prediction = get_price_predictions(surface, rooms, sector, insights)

    return prediction


@router.get('/analytics/similar/{listing_id}')
async def find_similar(
    listing_id: str,
    limit: int = Query(5, description="Maximum number of similar properties", ge=1, le=20)
):
    """
    Find similar properties for comparison.

    Finds properties with:
    - Surface area (±20%)
    - Number of rooms
    - Sector/location

    Returns similarity score (0-100) for each match.

    Args:
        listing_id: Property ID (url_slug) from proimobil API
        limit: Maximum number of results (default: 5)
    """
    # Get all listings
    listings = get_detailed_proimobil_api_listings()

    # Find target listing
    target_listing = None
    for listing in listings:
        if listing.get('url_slug') == listing_id or listing.get('id') == listing_id:
            target_listing = listing
            break

    if not target_listing:
        raise HTTPException(status_code=404, detail=f"Listing {listing_id} not found")

    # Find similar properties
    similar = find_similar_properties(target_listing, listings, limit)

    return {
        'reference_property': {
            'id': listing_id,
            'price_eur': target_listing['price_eur'],
            'price_per_sqm': target_listing['price_per_sqm'],
            'surface_sqm': target_listing['surface_sqm'],
            'rooms': target_listing.get('rooms'),
            'sector': target_listing.get('sector')
        },
        'similar_properties': similar,
        'total_found': len(similar)
    }


@router.get('/analytics/best-deals')
async def best_deals(
    limit: int = Query(10, description="Number of top deals to return", ge=1, le=50)
):
    """
    Find the best deals on the market.

    Returns properties with:
    - Highest overall investment scores
    - Best price vs market value
    - Good location and size scores

    Perfect for finding undervalued properties.

    Args:
        limit: Number of results (default: 10)
    """
    # Get listings and insights
    listings = get_detailed_proimobil_api_listings()

    if not listings:
        raise HTTPException(status_code=404, detail="No listings available")

    # Get market insights
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    cached_insights = cache.get('market_insights')
    if cached_insights:
        from app.services.market_analytics import MarketInsights
        insights = MarketInsights(**cached_insights)
    else:
        insights = analyze_market(listings)
        cache.set('market_insights', asdict(insights), source='api_request')

    # Score all properties
    scored_properties = []
    for listing in listings:
        score = score_property(listing, insights)
        scored_properties.append({
            'listing': listing,
            'score': asdict(score)
        })

    # Sort by overall score
    scored_properties.sort(key=lambda x: x['score']['overall_score'], reverse=True)

    # Return top N
    top_deals = scored_properties[:limit]

    return {
        'best_deals': top_deals,
        'total_analyzed': len(listings),
        'criteria': 'Overall investment score (price + location + size)'
    }
