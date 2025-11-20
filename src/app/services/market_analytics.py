"""
Advanced market analytics and predictions based on detailed property listings.
Provides insights, trends, investment scores, and price predictions.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


@dataclass
class MarketInsights:
    """Comprehensive market insights and analytics."""
    total_listings: int
    average_price_eur: float
    median_price_eur: float
    average_price_per_sqm: float
    median_price_per_sqm: float
    
    # Sector analysis
    sector_stats: Dict[str, Dict[str, Any]]
    top_sectors_by_volume: List[Tuple[str, int]]
    top_sectors_by_price: List[Tuple[str, float]]
    
    # Feature analysis
    average_surface: float
    room_distribution: Dict[int, int]
    most_common_rooms: int
    
    # Price distribution
    price_ranges: Dict[str, int]
    underpriced_count: int
    overpriced_count: int
    fair_priced_count: int
    
    # Trends
    premium_features: List[str]
    budget_indicators: List[str]
    
    # Investment insights
    best_value_sectors: List[Tuple[str, float]]  # sector, avg €/m²
    emerging_areas: List[str]


@dataclass
class PropertyScore:
    """Investment and value score for a property."""
    listing_id: str
    price_score: float  # 0-100, how good is the price
    location_score: float  # 0-100, how good is the location
    size_score: float  # 0-100, how optimal is the size
    overall_score: float  # 0-100, overall investment score
    value_assessment: str  # "excellent", "good", "fair", "poor"
    predicted_price_range: Tuple[float, float]
    vs_market_percentage: float  # +15% = overpriced, -10% = underpriced


def analyze_market(listings: List[Dict[str, Any]]) -> MarketInsights:
    """
    Perform comprehensive market analysis on property listings.
    
    Args:
        listings: List of property dictionaries from proimobil API
        
    Returns:
        MarketInsights with detailed analytics
    """
    if not listings:
        raise ValueError("No listings provided for analysis")
    
    # Basic stats
    total_listings = len(listings)
    prices = [l['price_eur'] for l in listings]
    prices_per_sqm = [l['price_per_sqm'] for l in listings if l['price_per_sqm'] > 0]
    surfaces = [l['surface_sqm'] for l in listings if l['surface_sqm'] > 0]
    
    # Sector analysis
    sector_data = defaultdict(lambda: {'prices': [], 'surfaces': [], 'count': 0})
    for listing in listings:
        sector = listing.get('sector', 'Unknown')
        sector_data[sector]['prices'].append(listing['price_eur'])
        sector_data[sector]['surfaces'].append(listing['surface_sqm'])
        sector_data[sector]['count'] += 1
    
    sector_stats = {}
    for sector, data in sector_data.items():
        if data['count'] > 0:
            avg_price = statistics.mean(data['prices'])
            avg_surface = statistics.mean(data['surfaces']) if data['surfaces'] else 0
            avg_price_sqm = avg_price / avg_surface if avg_surface > 0 else 0
            
            sector_stats[sector] = {
                'count': data['count'],
                'avg_price_eur': round(avg_price, 2),
                'avg_surface_sqm': round(avg_surface, 2),
                'avg_price_per_sqm': round(avg_price_sqm, 2),
                'min_price': min(data['prices']),
                'max_price': max(data['prices'])
            }
    
    # Top sectors
    top_sectors_by_volume = sorted(
        [(s, stats['count']) for s, stats in sector_stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    top_sectors_by_price = sorted(
        [(s, stats['avg_price_per_sqm']) for s, stats in sector_stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:5]
    
    # Room distribution
    room_counts = Counter(l['rooms'] for l in listings if l.get('rooms'))
    most_common_rooms = room_counts.most_common(1)[0][0] if room_counts else 2
    
    # Price ranges
    price_ranges = _calculate_price_ranges(prices)
    
    # Price assessment (underpriced/overpriced)
    median_price_sqm = statistics.median(prices_per_sqm) if prices_per_sqm else 0
    underpriced_count = sum(1 for p in prices_per_sqm if p < median_price_sqm * 0.85)
    overpriced_count = sum(1 for p in prices_per_sqm if p > median_price_sqm * 1.15)
    fair_priced_count = total_listings - underpriced_count - overpriced_count
    
    # Premium features (sectors with above average prices)
    avg_price_sqm = statistics.mean(prices_per_sqm) if prices_per_sqm else 0
    premium_features = [
        s for s, stats in sector_stats.items()
        if stats['avg_price_per_sqm'] > avg_price_sqm * 1.1
    ][:5]
    
    # Budget indicators
    budget_indicators = [
        s for s, stats in sector_stats.items()
        if stats['avg_price_per_sqm'] < avg_price_sqm * 0.9
    ][:5]
    
    # Best value sectors (good size, reasonable price)
    best_value = sorted(
        [(s, stats['avg_price_per_sqm']) for s, stats in sector_stats.items()
         if stats['avg_surface_sqm'] >= 45 and stats['count'] >= 3],
        key=lambda x: x[1]
    )[:5]
    
    # Emerging areas (moderate prices, good volume)
    emerging = [
        s for s, stats in sector_stats.items()
        if stats['count'] >= 5 and 
        avg_price_sqm * 0.9 <= stats['avg_price_per_sqm'] <= avg_price_sqm * 1.1
    ][:3]
    
    return MarketInsights(
        total_listings=total_listings,
        average_price_eur=round(statistics.mean(prices), 2),
        median_price_eur=round(statistics.median(prices), 2),
        average_price_per_sqm=round(avg_price_sqm, 2),
        median_price_per_sqm=round(median_price_sqm, 2),
        sector_stats=sector_stats,
        top_sectors_by_volume=top_sectors_by_volume,
        top_sectors_by_price=top_sectors_by_price,
        average_surface=round(statistics.mean(surfaces), 2) if surfaces else 0,
        room_distribution=dict(room_counts),
        most_common_rooms=most_common_rooms,
        price_ranges=price_ranges,
        underpriced_count=underpriced_count,
        overpriced_count=overpriced_count,
        fair_priced_count=fair_priced_count,
        premium_features=premium_features,
        budget_indicators=budget_indicators,
        best_value_sectors=best_value,
        emerging_areas=emerging
    )


def score_property(
    listing: Dict[str, Any],
    market_insights: MarketInsights
) -> PropertyScore:
    """
    Calculate investment and value scores for a property.
    
    Args:
        listing: Property listing dictionary
        market_insights: Market insights for comparison
        
    Returns:
        PropertyScore with detailed scoring
    """
    listing_id = listing.get('url_slug', listing.get('id', 'unknown'))
    price = listing['price_eur']
    surface = listing['surface_sqm']
    price_per_sqm = listing['price_per_sqm']
    sector = listing.get('sector', 'Unknown')
    rooms = listing.get('rooms', 2)
    
    # Price score (0-100): How good is the price vs market
    median_price_sqm = market_insights.median_price_per_sqm
    if price_per_sqm <= median_price_sqm * 0.85:
        price_score = 100  # Excellent deal
    elif price_per_sqm <= median_price_sqm:
        price_score = 85
    elif price_per_sqm <= median_price_sqm * 1.1:
        price_score = 70
    elif price_per_sqm <= median_price_sqm * 1.2:
        price_score = 50
    else:
        price_score = 30  # Overpriced
    
    # Location score (0-100): Based on sector popularity and price
    sector_stats = market_insights.sector_stats.get(sector)
    if sector_stats:
        # High volume + reasonable price = good location
        volume_score = min(100, (sector_stats['count'] / market_insights.total_listings) * 500)
        location_score = volume_score
    else:
        location_score = 50  # Unknown sector
    
    # Size score (0-100): How optimal is the size for the room count
    ideal_surface_per_room = 25  # ~25 sqm per room is ideal
    if rooms > 0:
        actual_surface_per_room = surface / rooms
        size_ratio = actual_surface_per_room / ideal_surface_per_room
        if 0.8 <= size_ratio <= 1.2:
            size_score = 100
        elif 0.6 <= size_ratio <= 1.4:
            size_score = 80
        else:
            size_score = 60
    else:
        size_score = 70
    
    # Overall score (weighted average)
    overall_score = (
        price_score * 0.5 +  # Price is most important
        location_score * 0.3 +
        size_score * 0.2
    )
    
    # Value assessment
    if overall_score >= 85:
        value_assessment = "excellent"
    elif overall_score >= 70:
        value_assessment = "good"
    elif overall_score >= 50:
        value_assessment = "fair"
    else:
        value_assessment = "poor"
    
    # Predicted price range (±10% confidence interval)
    predicted_price = median_price_sqm * surface
    predicted_range = (
        round(predicted_price * 0.9, 2),
        round(predicted_price * 1.1, 2)
    )
    
    # Vs market percentage
    vs_market = ((price_per_sqm - median_price_sqm) / median_price_sqm) * 100
    
    return PropertyScore(
        listing_id=listing_id,
        price_score=round(price_score, 1),
        location_score=round(location_score, 1),
        size_score=round(size_score, 1),
        overall_score=round(overall_score, 1),
        value_assessment=value_assessment,
        predicted_price_range=predicted_range,
        vs_market_percentage=round(vs_market, 1)
    )


def get_price_predictions(
    target_surface: float,
    target_rooms: int,
    target_sector: Optional[str],
    market_insights: MarketInsights
) -> Dict[str, Any]:
    """
    Predict price for a hypothetical property based on characteristics.
    
    Args:
        target_surface: Desired surface area in sqm
        target_rooms: Number of rooms
        target_sector: Desired sector (optional)
        market_insights: Market insights for prediction
        
    Returns:
        Price prediction with confidence intervals
    """
    # Base prediction on median price per sqm
    base_price_sqm = market_insights.median_price_per_sqm
    
    # Adjust for sector if specified
    if target_sector and target_sector in market_insights.sector_stats:
        sector_stats = market_insights.sector_stats[target_sector]
        sector_price_sqm = sector_stats['avg_price_per_sqm']
        # Weight sector price more if it has many listings
        if sector_stats['count'] >= 5:
            base_price_sqm = (base_price_sqm * 0.3 + sector_price_sqm * 0.7)
        else:
            base_price_sqm = (base_price_sqm * 0.6 + sector_price_sqm * 0.4)
    
    # Adjust for size (larger apartments usually cheaper per sqm)
    if target_surface > 60:
        size_factor = 0.95
    elif target_surface < 40:
        size_factor = 1.05
    else:
        size_factor = 1.0
    
    adjusted_price_sqm = base_price_sqm * size_factor
    
    # Calculate predicted price
    predicted_price = adjusted_price_sqm * target_surface
    
    # Confidence intervals
    conservative = predicted_price * 0.85
    optimistic = predicted_price * 1.15
    
    return {
        'predicted_price_eur': round(predicted_price, 2),
        'predicted_price_per_sqm': round(adjusted_price_sqm, 2),
        'confidence_interval': {
            'min': round(conservative, 2),
            'max': round(optimistic, 2),
            'confidence': '85%'
        },
        'inputs': {
            'surface_sqm': target_surface,
            'rooms': target_rooms,
            'sector': target_sector or 'Market average'
        },
        'market_comparison': {
            'vs_market_median': f"{((adjusted_price_sqm - market_insights.median_price_per_sqm) / market_insights.median_price_per_sqm * 100):.1f}%",
            'market_median_price_sqm': market_insights.median_price_per_sqm
        }
    }


def find_similar_properties(
    reference_listing: Dict[str, Any],
    all_listings: List[Dict[str, Any]],
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find similar properties for comparison.
    
    Args:
        reference_listing: The property to compare against
        all_listings: All available listings
        limit: Maximum number of similar properties to return
        
    Returns:
        List of similar properties with similarity scores
    """
    ref_surface = reference_listing['surface_sqm']
    ref_rooms = reference_listing.get('rooms', 2)
    ref_sector = reference_listing.get('sector', '')
    
    similar = []
    
    for listing in all_listings:
        if listing.get('url_slug') == reference_listing.get('url_slug'):
            continue  # Skip self
        
        # Calculate similarity score
        surface_diff = abs(listing['surface_sqm'] - ref_surface) / ref_surface
        rooms_match = 1.0 if listing.get('rooms') == ref_rooms else 0.5
        sector_match = 1.0 if listing.get('sector') == ref_sector else 0.3
        
        # Similarity score (0-100)
        similarity = (
            (1 - min(surface_diff, 1.0)) * 40 +  # Surface: 40%
            rooms_match * 30 +  # Rooms: 30%
            sector_match * 30  # Sector: 30%
        )
        
        if similarity >= 40:  # Only include reasonably similar properties
            similar.append({
                **listing,
                'similarity_score': round(similarity, 1)
            })
    
    # Sort by similarity and return top N
    similar.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar[:limit]


def _calculate_price_ranges(prices: List[float]) -> Dict[str, int]:
    """Calculate distribution across price ranges."""
    ranges = {
        'under_50k': 0,
        '50k_70k': 0,
        '70k_90k': 0,
        '90k_120k': 0,
        'over_120k': 0
    }
    
    for price in prices:
        if price < 50000:
            ranges['under_50k'] += 1
        elif price < 70000:
            ranges['50k_70k'] += 1
        elif price < 90000:
            ranges['70k_90k'] += 1
        elif price < 120000:
            ranges['90k_120k'] += 1
        else:
            ranges['over_120k'] += 1
    
    return ranges

