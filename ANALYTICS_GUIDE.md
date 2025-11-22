# 📊 Market Analytics API - Usage Examples

## Overview

The Analytics API provides advanced market intelligence, investment scoring, and price predictions based on real market data from proimobil.md.

## 🔍 Endpoints

### 1. Market Insights

Get comprehensive market analysis including sector statistics, price distributions, and trends.

**Endpoint**: `GET /market/analytics/insights`

**Example Request**:
```bash
curl http://localhost:8000/market/analytics/insights
```

**Example Response**:
```json
{
  "total_listings": 600,
  "average_price_eur": 95000.50,
  "median_price_eur": 85000.00,
  "average_price_per_sqm": 1750.25,
  "median_price_per_sqm": 1650.00,
  "sector_stats": {
    "Botanica": {
      "count": 45,
      "avg_price_eur": 88000.00,
      "avg_surface_sqm": 52.5,
      "avg_price_per_sqm": 1676.19,
      "min_price": 55000,
      "max_price": 125000
    },
    "Centru": {
      "count": 38,
      "avg_price_eur": 105000.00,
      "avg_surface_sqm": 50.0,
      "avg_price_per_sqm": 2100.00,
      "min_price": 75000,
      "max_price": 145000
    }
  },
  "top_sectors_by_volume": [
    ["Botanica", 45],
    ["Centru", 38],
    ["Râșcani", 35]
  ],
  "top_sectors_by_price": [
    ["Centru", 2100.00],
    ["Buiucani", 1850.00],
    ["Botanica", 1676.19]
  ],
  "room_distribution": {
    "1": 85,
    "2": 320,
    "3": 165,
    "4": 30
  },
  "most_common_rooms": 2,
  "price_ranges": {
    "under_50k": 12,
    "50k_70k": 125,
    "70k_90k": 235,
    "90k_120k": 185,
    "over_120k": 43
  },
  "underpriced_count": 78,
  "overpriced_count": 65,
  "fair_priced_count": 457,
  "premium_features": ["Centru", "Buiucani"],
  "budget_indicators": ["Ciocana", "Poșta Veche"],
  "best_value_sectors": [
    ["Botanica", 1676.19],
    ["Râșcani", 1720.50]
  ],
  "emerging_areas": ["Botanica", "Râșcani"]
}
```

**Use Cases**:
- Market research and analysis
- Identifying trending sectors
- Understanding price distributions
- Finding investment opportunities

---

### 2. Property Investment Score

Get a comprehensive investment score (0-100) for any property.

**Endpoint**: `GET /market/analytics/property-score/{listing_id}`

**Example Request**:
```bash
# Using ID
curl http://localhost:8000/market/analytics/property-score/12345

# Or using URL slug
curl http://localhost:8000/market/analytics/property-score/apartament-cu-2-odai-de-vanzare-in-chisinau-botanica
```

**Note**: You can use either the `id` or `url_slug` from `/market/proimobil-api/listings` response.

**Example Response**:
```json
{
  "listing_id": "apartament-cu-2-odai-de-vanzare-in-chisinau-botanica",
  "price_score": 85.0,
  "location_score": 72.5,
  "size_score": 90.0,
  "overall_score": 82.4,
  "value_assessment": "good",
  "predicted_price_range": [76500.00, 93500.00],
  "vs_market_percentage": -8.5,
  "listing_details": {
    "price_eur": 82000,
    "price_per_sqm": 1509.09,
    "surface_sqm": 54.3,
    "rooms": 2,
    "sector": "Botanica",
    "street": "str. Decebal"
  }
}
```

**Score Interpretation**:
- **90-100**: Excellent investment opportunity
- **70-89**: Good value
- **50-69**: Fair market price
- **Below 50**: Overpriced

**Components**:
- `price_score`: How competitive is the price vs market (50% weight)
- `location_score`: Desirability of sector/location (30% weight)
- `size_score`: Optimal size for room count (20% weight)
- `vs_market_percentage`: Negative = underpriced, Positive = overpriced

**Use Cases**:
- Evaluate investment potential
- Compare properties objectively
- Negotiate prices with data
- Identify undervalued properties

---

### 3. Price Prediction

Predict property price based on characteristics using statistical analysis.

**Endpoint**: `GET /market/analytics/predict-price`

**Parameters**:
- `surface` (required): Surface area in sqm
- `rooms` (required): Number of rooms
- `sector` (optional): Sector/neighborhood name

**Example Request**:
```bash
curl "http://localhost:8000/market/analytics/predict-price?surface=55&rooms=2&sector=Botanica"
```

**Example Response**:
```json
{
  "predicted_price_eur": 89375.00,
  "predicted_price_per_sqm": 1625.00,
  "confidence_interval": {
    "min": 75968.75,
    "max": 102781.25,
    "confidence": "85%"
  },
  "inputs": {
    "surface_sqm": 55,
    "rooms": 2,
    "sector": "Botanica"
  },
  "market_comparison": {
    "vs_market_median": "-1.5%",
    "market_median_price_sqm": 1650.00
  }
}
```

**Use Cases**:
- Estimate fair market value
- Set listing prices
- Evaluate offers
- Budget planning for buyers

---

### 4. Find Similar Properties

Find properties similar to a reference property for comparison.

**Endpoint**: `GET /market/analytics/similar/{listing_id}`

**Parameters**:
- `limit` (optional): Max number of results (default: 5, max: 20)

**Example Request**:
```bash
curl "http://localhost:8000/market/analytics/similar/apartament-cu-2-odai-de-vanzare-in-chisinau-botanica?limit=3"
```

**Example Response**:
```json
{
  "reference_property": {
    "id": "apartament-cu-2-odai-de-vanzare-in-chisinau-botanica",
    "price_eur": 82000,
    "price_per_sqm": 1509.09,
    "surface_sqm": 54.3,
    "rooms": 2,
    "sector": "Botanica"
  },
  "similar_properties": [
    {
      "price_eur": 85000,
      "price_per_sqm": 1562.50,
      "surface_sqm": 54.4,
      "rooms": 2,
      "sector": "Botanica",
      "street": "str. Dacia",
      "url_slug": "apartament-2-odai-botanica-dacia",
      "similarity_score": 95.8
    },
    {
      "price_eur": 79000,
      "price_per_sqm": 1481.13,
      "surface_sqm": 53.3,
      "rooms": 2,
      "sector": "Botanica",
      "street": "str. Trandafirilor",
      "url_slug": "apartament-2-camere-botanica",
      "similarity_score": 92.3
    }
  ],
  "total_found": 2
}
```

**Similarity Algorithm**:
- Surface area: 40% weight (±20% tolerance)
- Rooms match: 30% weight
- Same sector: 30% weight
- Minimum score: 40

**Use Cases**:
- Price comparison
- Market research
- Validate listings
- Find alternatives

---

### 5. Best Deals

Find the top investment opportunities on the market.

**Endpoint**: `GET /market/analytics/best-deals`

**Parameters**:
- `limit` (optional): Number of results (default: 10, max: 50)

**Example Request**:
```bash
curl "http://localhost:8000/market/analytics/best-deals?limit=5"
```

**Example Response**:
```json
{
  "best_deals": [
    {
      "listing": {
        "price_eur": 75000,
        "price_per_sqm": 1388.89,
        "surface_sqm": 54.0,
        "rooms": 2,
        "sector": "Botanica",
        "street": "str. Alba Iulia",
        "url_slug": "apartament-botanica-alba-iulia"
      },
      "score": {
        "overall_score": 92.5,
        "price_score": 100.0,
        "location_score": 75.0,
        "size_score": 95.0,
        "value_assessment": "excellent",
        "predicted_price_range": [81000.00, 99000.00],
        "vs_market_percentage": -15.8
      }
    }
  ],
  "total_analyzed": 600,
  "criteria": "Overall investment score (price + location + size)"
}
```

**Use Cases**:
- Find undervalued properties
- Investment opportunity scanning
- Market inefficiency detection
- Quick deal identification

---

## 🎯 Common Use Cases

### 1. Research a Sector

```bash
# Get market insights
curl http://localhost:8000/market/analytics/insights | jq '.sector_stats.Botanica'

# See top sectors
curl http://localhost:8000/market/analytics/insights | jq '.top_sectors_by_volume'
```

### 2. Evaluate a Property

```bash
# Get property score
LISTING_ID="apartament-2-odai-botanica"
curl http://localhost:8000/market/analytics/property-score/$LISTING_ID

# Find similar properties
curl http://localhost:8000/market/analytics/similar/$LISTING_ID
```

### 3. Price Estimation

```bash
# Predict price for 2-room, 55sqm apartment in Botanica
curl "http://localhost:8000/market/analytics/predict-price?surface=55&rooms=2&sector=Botanica"
```

### 4. Find Investment Opportunities

```bash
# Get best deals
curl http://localhost:8000/market/analytics/best-deals?limit=10

# Filter by score
curl http://localhost:8000/market/analytics/best-deals | jq '.best_deals[] | select(.score.overall_score >= 85)'
```

---

## 📈 Integration Examples

### Python

```python
import requests

# Get market insights
response = requests.get("http://localhost:8000/market/analytics/insights")
insights = response.json()

print(f"Total listings: {insights['total_listings']}")
print(f"Median price: €{insights['median_price_eur']}")
print(f"Top sector: {insights['top_sectors_by_volume'][0]}")

# Predict price
params = {
    "surface": 55,
    "rooms": 2,
    "sector": "Botanica"
}
response = requests.get("http://localhost:8000/market/analytics/predict-price", params=params)
prediction = response.json()

print(f"Predicted price: €{prediction['predicted_price_eur']}")
print(f"Range: €{prediction['confidence_interval']['min']} - €{prediction['confidence_interval']['max']}")
```

### JavaScript/TypeScript

```typescript
// Get property score
const listingId = "apartament-2-odai-botanica";
const response = await fetch(
  `http://localhost:8000/market/analytics/property-score/${listingId}`
);
const score = await response.json();

console.log(`Overall score: ${score.overall_score}/100`);
console.log(`Value assessment: ${score.value_assessment}`);
console.log(`Market comparison: ${score.vs_market_percentage}%`);

// Find best deals
const dealsResponse = await fetch(
  "http://localhost:8000/market/analytics/best-deals?limit=5"
);
const deals = await dealsResponse.json();

deals.best_deals.forEach(deal => {
  console.log(`${deal.listing.sector} - €${deal.listing.price_eur}`);
  console.log(`Score: ${deal.score.overall_score}/100`);
});
```

---

## 🔄 Caching

All analytics endpoints use intelligent caching:
- **Cache TTL**: 30 minutes
- **Auto-refresh**: Background scheduler updates every 30 minutes
- **Consistency**: All endpoints use same cached market insights

To force refresh:
```bash
curl -X POST http://localhost:8000/cache/refresh
```

---

## 📊 Data Quality

- **Source**: Proimobil.md official API
- **Update frequency**: Every 30 minutes
- **Coverage**: 500+ active listings
- **Accuracy**: Based on real market data, not estimates
- **Sectors**: All major Chișinău sectors

---

## 💡 Tips

1. **Use sector parameter** in predictions for more accurate results
2. **Check similarity_score** when comparing properties (>70 = good match)
3. **Combine endpoints** for comprehensive analysis
4. **Monitor best_deals** regularly for new opportunities
5. **Compare overall_score** across properties for objective evaluation

---

## 🆘 Support

For questions or issues:
- Check API docs: http://localhost:8000/docs
- Open an issue on GitHub
- Review test examples in `tests/test_analytics.py`

