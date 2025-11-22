import statistics

from fastapi import APIRouter, Query, HTTPException
from app.core.config import get_settings
from app.scraping.proimobil import compute_proimobil_stats
from app.scraping.accesimobil import compute_stats_for_accesimobil
from app.scraping.md999 import compute_999md_stats, fetch_all_999md_prices
from app.services.cache import get_market_cache
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
    find_similar_properties,
    MarketInsights
)
from typing import Optional
from dataclasses import asdict
from datetime import datetime, timezone, timedelta


def _get_proimobil_api_listings():
    """
    Common helper for all Proimobil API routes.
    Gets the data from the cache ('proimobil_api_listings'), and if it doesn't exist,
    calls get_detailed_proimobil_api_listings().
    """
    cache = get_market_cache()
    cached_data = cache.get('proimobil_api_listings')

    if cached_data:
        return cached_data.get('listings', [])
    return get_detailed_proimobil_api_listings()


def _safe_mean(values):
    values = [v for v in values if v is not None]
    return statistics.mean(values) if values else None


def _safe_median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None

def _compute_price_analysis(listings):
    """
    Price analysis:
    - price_per_sqm global
    - per sector / condition / state / rooms / floor_category
    - surface buckets (<40, 40-60, 60-80, 80+)
    """
    price_per_sqm_all = []
    by_sector = {}
    by_condition = {}
    by_state = {}
    by_rooms = {}
    by_floor_cat = {}
    by_surface_bucket = {}
    surface_all = []

    def floor_category(floor, number_of_floors):
        if floor is None:
            return 'unknown'
        if floor == 1:
            return 'first'
        if number_of_floors and floor == number_of_floors:
            return 'last'
        return 'other'

    def surface_bucket(surface):
        if surface is None:
            return 'unknown'
        if surface < 40:
            return '<40'
        if surface < 60:
            return '40-60'
        if surface < 80:
            return '60-80'
        return '80+'

    for l in listings:
        price_per_sqm = l.get('price_per_sqm')
        surface = l.get('surface_sqm')
        sector = l.get('sector')
        condition = l.get('condition')
        state = l.get('state')
        rooms = l.get('rooms')
        floor = l.get('floor')
        number_of_floors = l.get('number_of_floors')

        if price_per_sqm is not None:
            price_per_sqm_all.append(price_per_sqm)

        if surface is not None:
            surface_all.append(surface)

        if sector and price_per_sqm is not None:
            by_sector.setdefault(sector, []).append(price_per_sqm)

        if condition and price_per_sqm is not None:
            by_condition.setdefault(condition, []).append(price_per_sqm)

        if state and price_per_sqm is not None:
            by_state.setdefault(state, []).append(price_per_sqm)

        if rooms is not None and price_per_sqm is not None:
            by_rooms.setdefault(str(rooms), []).append(price_per_sqm)

        fc = floor_category(floor, number_of_floors)
        if price_per_sqm is not None:
            by_floor_cat.setdefault(fc, []).append(price_per_sqm)

        sb = surface_bucket(surface)
        if price_per_sqm is not None:
            by_surface_bucket.setdefault(sb, []).append(price_per_sqm)

    def build_group_stats(group_dict):
        result = {}
        for key, vals in group_dict.items():
            result[key] = {
                'mean_price_per_sqm': _safe_mean(vals),
                'median_price_per_sqm': _safe_median(vals),
                'count': len(vals),
            }
        return result

    price_stats_global = {
        'mean_price_per_sqm': _safe_mean(price_per_sqm_all),
        'median_price_per_sqm': _safe_median(price_per_sqm_all),
        'min_price_per_sqm': min(price_per_sqm_all, default=None),
        'max_price_per_sqm': max(price_per_sqm_all, default=None),
        'count': len(price_per_sqm_all),
    }

    surface_stats = {
        'mean_surface_sqm': _safe_mean(surface_all),
        'median_surface_sqm': _safe_median(surface_all),
        'min_surface_sqm': min(surface_all, default=None),
        'max_surface_sqm': max(surface_all, default=None),
        'count': len(surface_all),
        'buckets': {
            b: {
                'count': len(vals),
                'mean_price_per_sqm': _safe_mean(vals),
                'median_price_per_sqm': _safe_median(vals),
            }
            for b, vals in by_surface_bucket.items()
        }
    }

    return {
        'total_listings': len(listings),
        'price_per_sqm_global': price_stats_global,
        'price_per_sqm_by': {
            'sector': build_group_stats(by_sector),
            'condition': build_group_stats(by_condition),
            'state': build_group_stats(by_state),
            'rooms': build_group_stats(by_rooms),
            'floor_category': build_group_stats(by_floor_cat),
        },
        'surface_stats': surface_stats,
    }


def _compute_deal_scoring(listings):
    """
    Deal scoring:
    - baseline price_per_sqm by (sector, rooms)
    - conversion by sector / condition / state
    - below-market pct & score per listing
    - best_deals (top 20)
    """
    now = datetime.now(timezone.utc)

    # 1) Baseline price_per_sqm by (sector, rooms)
    grouped = {}
    baseline = {}

    for l in listings:
        sector = l.get('sector') or 'unknown'
        rooms = l.get('rooms')
        price_per_sqm = l.get('price_per_sqm')

        if rooms is None or price_per_sqm is None:
            continue

        key = (sector, int(rooms))
        grouped.setdefault(key, []).append(price_per_sqm)

    for key, vals in grouped.items():
        baseline[key] = _safe_mean(vals)

    # 2) Sale / booked stats by sector / condition / state
    by_sector = {}
    by_condition = {}
    by_state = {}

    def update_group(group_dict, key, booked, sold):
        if key is None:
            key = 'unknown'
        stats = group_dict.setdefault(key, {'total': 0, 'booked': 0, 'sold': 0})
        stats['total'] += 1
        if booked:
            stats['booked'] += 1
        if sold:
            stats['sold'] += 1

    scored_listings = []
    total_listings = len(listings)

    for l in listings:
        sector = l.get('sector') or 'unknown'
        rooms = l.get('rooms')
        condition = l.get('condition')
        state = l.get('state')
        price = l.get('price_eur')
        price_per_sqm = l.get('price_per_sqm')
        views = l.get('views') or 0
        booked = bool(l.get('booked'))
        sold = bool(l.get('deal'))

        created_raw = l.get('created_at')
        try:
            created = datetime.fromisoformat(created_raw.replace('Z', '+00:00')) if created_raw else None
        except Exception:
            created = None

        days_on_market = (now - created).days if created else None
        views_per_day = None
        if days_on_market and days_on_market > 0:
            views_per_day = views / days_on_market

        update_group(by_sector, sector, booked, sold)
        update_group(by_condition, condition, booked, sold)
        update_group(by_state, state, booked, sold)

        below_market_pct = None
        score = None

        if rooms is not None and price_per_sqm is not None:
            key = (sector, int(rooms))
            base = baseline.get(key)
            if base:
                below_market_pct = (price_per_sqm - base) / base * 100
                base_component = -below_market_pct   # sub piață => pozitiv
                engagement_component = (views_per_day or 0)
                score = base_component + engagement_component

        scored_listings.append({
            'id': l['id'],
            'sector': sector,
            'rooms': rooms,
            'condition': condition,
            'state': state,
            'price_eur': price,
            'price_per_sqm': price_per_sqm,
            'views': views,
            'views_per_day': views_per_day,
            'booked': booked,
            'sold': sold,
            'days_on_market': days_on_market,
            'below_market_pct': below_market_pct,
            'score': score,
        })

    def finalize_group_stats(group_dict):
        result = {}
        for key, s in group_dict.items():
            total = s['total']
            booked = s['booked']
            sold = s['sold']
            result[key] = {
                'total': total,
                'booked': booked,
                'sold': sold,
                'booked_rate': booked / total if total else None,
                'sold_rate': sold / total if total else None,
            }
        return result

    by_sector_stats = finalize_group_stats(by_sector)
    by_condition_stats = finalize_group_stats(by_condition)
    by_state_stats = finalize_group_stats(by_state)

    best_deals = sorted(
        [s for s in scored_listings if s['score'] is not None],
        key=lambda x: x['score'],
        reverse=True
    )[:20]

    return {
        'total_listings': total_listings,
        'baselines': {
            'by_sector_and_rooms': {
                f'{sector}|{rooms}': value
                for (sector, rooms), value in baseline.items()
            }
        },
        'conversion': {
            'by_sector': by_sector_stats,
            'by_condition': by_condition_stats,
            'by_state': by_state_stats,
        },
        'best_deals': best_deals,
        'scored_sample_size': len([s for s in scored_listings if s['score'] is not None]),
        'scored_listings': scored_listings,  # îl folosim pentru time-to-sell / health
    }


def _compute_investment_insights(listings):
    """
    Investment insights:
    - per sector: price_per_sqm + days_on_market + booked/sold rates
    - attractiveness_score (ieftin + se vinde relativ repede)
    - ROI placeholders (None, până ai chirii)
    """
    now = datetime.now(timezone.utc)
    sectors = {}

    for l in listings:
        sector = l.get('sector') or 'unknown'
        s = sectors.setdefault(sector, {
            'price_per_sqm': [],
            'days_on_market': [],
            'total': 0,
            'booked': 0,
            'sold': 0,
        })

        s['total'] += 1

        pps = l.get('price_per_sqm')
        if pps is not None:
            s['price_per_sqm'].append(pps)

        created_raw = l.get('created_at')
        try:
            created = datetime.fromisoformat(created_raw.replace('Z', '+00:00')) if created_raw else None
        except Exception:
            created = None

        if created:
            dom = (now - created).days
            s['days_on_market'].append(dom)

        if l.get('booked'):
            s['booked'] += 1
        if l.get('deal'):
            s['sold'] += 1

    sector_insights = {}
    for sector, s in sectors.items():
        total = s['total']
        price_list = s['price_per_sqm']
        dom_list = s['days_on_market']
        booked = s['booked']
        sold = s['sold']

        avg_price = _safe_mean(price_list)
        avg_dom = _safe_mean(dom_list)
        booked_rate = booked / total if total else None
        sold_rate = sold / total if total else None

        attractiveness = None
        if avg_price and avg_dom and sold_rate is not None:
            attractiveness = (sold_rate * 1000) - (avg_price / 1000.0) - avg_dom

        sector_insights[sector] = {
            'total_listings': total,
            'avg_price_per_sqm': avg_price,
            'median_price_per_sqm': _safe_median(price_list),
            'avg_days_on_market': avg_dom,
            'median_days_on_market': _safe_median(dom_list),
            'booked_rate': booked_rate,
            'sold_rate': sold_rate,
            'attractiveness_score': attractiveness,
            'estimated_gross_yield': None,
            'estimated_payback_years': None,
        }

    ranked_sectors = sorted(
        [(sec, v) for sec, v in sector_insights.items() if v['attractiveness_score'] is not None],
        key=lambda x: x[1]['attractiveness_score'],
        reverse=True
    )

    return {
        'sector_insights': sector_insights,
        'top_sectors_by_attractiveness': [
            {'sector': sec, **vals} for sec, vals in ranked_sectors[:10]
        ],
        'note': 'ROI fields are placeholders (require rent data).',
    }


def _compute_trends(listings, days_back=30):
    """
    Trends (snapshot-based):
    - created_per_day, updated_per_day pentru ultimele days_back zile
    - price_per_sqm by age bucket (0-7, 8-30, >30)
    """
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(days=days_back)).date()

    created_per_day = {}
    updated_per_day = {}
    age_bucket_prices = {'0-7': [], '8-30': [], '>30': []}

    for i in range(days_back + 1):
        d = start_date + timedelta(days=i)
        created_per_day[d.isoformat()] = 0
        updated_per_day[d.isoformat()] = 0

    for l in listings:
        created_raw = l.get('created_at')
        updated_raw = l.get('updated_at')
        price_per_sqm = l.get('price_per_sqm')

        created_dt = None
        if created_raw:
            try:
                created_dt = datetime.fromisoformat(created_raw.replace('Z', '+00:00'))
            except Exception:
                created_dt = None

        if created_dt:
            created_date = created_dt.date()
            if start_date <= created_date <= now.date():
                created_per_day[created_date.isoformat()] = created_per_day.get(created_date.isoformat(), 0) + 1

        updated_dt = None
        if updated_raw:
            try:
                updated_dt = datetime.fromisoformat(updated_raw.replace('Z', '+00:00'))
            except Exception:
                updated_dt = None

        if updated_dt:
            updated_date = updated_dt.date()
            if start_date <= updated_date <= now.date():
                updated_per_day[updated_date.isoformat()] = updated_per_day.get(updated_date.isoformat(), 0) + 1

        if created_dt and price_per_sqm is not None:
            age_days = (now - created_dt).days
            if age_days <= 7:
                age_bucket_prices['0-7'].append(price_per_sqm)
            elif age_days <= 30:
                age_bucket_prices['8-30'].append(price_per_sqm)
            else:
                age_bucket_prices['>30'].append(price_per_sqm)

    age_buckets_stats = {
        bucket: {
            'count': len(vals),
            'mean_price_per_sqm': _safe_mean(vals),
        }
        for bucket, vals in age_bucket_prices.items()
    }

    return {
        'window_days': days_back,
        'created_per_day': created_per_day,
        'updated_per_day': updated_per_day,
        'price_per_sqm_by_age_bucket': age_buckets_stats,
        'note': 'Full price trends and price change detection require storing historical snapshots in DB.',
    }


def _compute_market_health_and_time_to_sell(listings, scored_listings_from_deal):
    """
    - Market Health Score + Stress Index pe sector
    - Time-to-sell model:
        * global_median_days_until_sold
        * per segment (sector|rooms)
        * sample_predictions pentru câteva anunțuri active
    """
    now = datetime.now(timezone.utc)

    # 1) extract only sold ads (deal == True) for time-to-sell
    sold_samples = []
    for l in listings:
        if not l.get('deal'):
            continue

        created_raw = l.get('created_at')
        updated_raw = l.get('updated_at')
        try:
            created = datetime.fromisoformat(created_raw.replace('Z', '+00:00')) if created_raw else None
            updated = datetime.fromisoformat(updated_raw.replace('Z', '+00:00')) if updated_raw else None
        except Exception:
            created = updated = None

        if created and updated:
            days_until_sold = (updated - created).days
            sold_samples.append({
                'sector': l.get('sector') or 'unknown',
                'rooms': l.get('rooms'),
                'days_until_sold': days_until_sold,
            })

    global_median_days_until_sold = _safe_median([s['days_until_sold'] for s in sold_samples])

    # 2) time-to-sell pe segmente (sector, rooms)
    segments = {}
    for s in sold_samples:
        sector = s['sector']
        rooms = s['rooms']
        if rooms is None:
            continue
        key = (sector, int(rooms))
        seg = segments.setdefault(key, [])
        seg.append(s['days_until_sold'])

    segment_stats = {}
    for (sector, rooms), vals in segments.items():
        segment_stats[f'{sector}|{rooms}'] = {
            'median_days_until_sold': _safe_median(vals),
            'sample_size': len(vals),
        }

    # 3) sample predictions for some active ads (deal=False)
    sample_predictions = []
    for s in scored_listings_from_deal:
        if s.get('sold'):
            continue  # deja vândut

        sector = s.get('sector') or 'unknown'
        rooms = s.get('rooms')
        if rooms is None:
            continue

        key = f'{sector}|{rooms}'
        seg = segment_stats.get(key)
        if seg:
            pred = seg['median_days_until_sold']
            support = seg['sample_size']
        else:
            pred = global_median_days_until_sold
            support = 0

        if pred is None:
            continue

        if support >= 20:
            confidence = 'high'
        elif support >= 5:
            confidence = 'medium'
        elif support >= 1:
            confidence = 'low'
        else:
            confidence = 'very_low'

        sample_predictions.append({
            'id': s['id'],
            'sector': sector,
            'rooms': rooms,
            'price_per_sqm': s.get('price_per_sqm'),
            'days_on_market': s.get('days_on_market'),
            'predicted_days_to_sell': pred,
            'segment_key': key if seg else 'GLOBAL',
            'segment_sample_size': support,
            'confidence': confidence,
        })

    sample_predictions = sample_predictions[:1000]

    # 4) Market Health & Stress Index pe sector
    # definim:
    # - new_last_30 = create în ultimele 30 zile
    # - sold_last_30 = deal=True cu updated în ultimele 30 zile
    # - avg_dom = medie DOM
    # - stress_index = active_listings / max(sold_last_30, 1)
    # - health_score = sold_last_30 - (avg_dom / 2) + new_last_30 * 0.2 (heuristic simplu)
    start_30 = (now - timedelta(days=30))

    sectors = {}
    for l in listings:
        sector = l.get('sector') or 'unknown'
        s = sectors.setdefault(sector, {
            'active': 0,
            'new_last_30': 0,
            'sold_last_30': 0,
            'dom_list': [],
        })
        s['active'] += 1

        created_raw = l.get('created_at')
        updated_raw = l.get('updated_at')
        try:
            created = datetime.fromisoformat(created_raw.replace('Z', '+00:00')) if created_raw else None
            updated = datetime.fromisoformat(updated_raw.replace('Z', '+00:00')) if updated_raw else None
        except Exception:
            created = updated = None

        if created and created >= start_30:
            s['new_last_30'] += 1

        if l.get('deal') and updated and updated >= start_30:
            s['sold_last_30'] += 1

        if created:
            dom = (now - created).days
            s['dom_list'].append(dom)

    by_sector = {}
    global_scores = []

    for sector, s in sectors.items():
        avg_dom = _safe_mean(s['dom_list'])
        sold_last_30 = s['sold_last_30']
        new_last_30 = s['new_last_30']
        active = s['active']
        stress_index = active / max(sold_last_30, 1)  # mai mare => mai multă „presiune”

        health_score = None
        if avg_dom is not None:
            health_score = (sold_last_30 * 10) - (avg_dom * 0.5) + (new_last_30 * 0.2)

        by_sector[sector] = {
            'active_listings': active,
            'new_last_30': new_last_30,
            'sold_last_30': sold_last_30,
            'avg_days_on_market': avg_dom,
            'stress_index': stress_index,
            'health_score': health_score,
        }
        if health_score is not None:
            global_scores.append(health_score)

    global_health_score = _safe_mean(global_scores)

    return {
        'market_health': {
            'global_health_score': global_health_score,
            'by_sector': by_sector,
        },
        'time_to_sell_model': {
            'global_median_days_until_sold': global_median_days_until_sold,
            'segments': segment_stats,
            'sample_predictions': sample_predictions,
        },
    }




def _reconstruct_market_insights(cached_data: dict) -> MarketInsights:
    """Reconstruct MarketInsights from cached dict, filtering extra keys."""
    valid_fields = {
        'total_listings', 'average_price_eur', 'median_price_eur',
        'average_price_per_sqm', 'median_price_per_sqm', 'sector_stats',
        'top_sectors_by_volume', 'top_sectors_by_price', 'average_surface',
        'room_distribution', 'most_common_rooms', 'price_ranges',
        'underpriced_count', 'overpriced_count', 'fair_priced_count',
        'premium_features', 'budget_indicators', 'best_value_sectors',
        'emerging_areas'
    }
    filtered = {k: v for k, v in cached_data.items() if k in valid_fields}
    return MarketInsights(**filtered)

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

    # Get listings from cache or fetch fresh
    cached_listings_data = cache.get('proimobil_api_listings')
    if cached_listings_data:
        listings = cached_listings_data.get('listings', [])
    else:
        # Cache miss - fetch fresh
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
        listing_id: Property ID or url_slug from proimobil API
    """
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    # Get listings from cache
    cached_listings_data = cache.get('proimobil_api_listings')
    if cached_listings_data:
        listings = cached_listings_data.get('listings', [])
    else:
        # Cache miss - fetch fresh
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
        insights = _reconstruct_market_insights(cached_insights)
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
        insights = _reconstruct_market_insights(cached_insights)
    else:
        # Get listings from cache
        cached_listings_data = cache.get('proimobil_api_listings')
        if cached_listings_data:
            listings = cached_listings_data.get('listings', [])
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
        listing_id: Property ID or url_slug from proimobil API
        limit: Maximum number of results (default: 5)
    """
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    # Get all listings from cache
    cached_listings_data = cache.get('proimobil_api_listings')
    if cached_listings_data:
        listings = cached_listings_data.get('listings', [])
    else:
        # Cache miss - fetch fresh
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
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    # Get listings from cache
    cached_listings_data = cache.get('proimobil_api_listings')
    if cached_listings_data:
        listings = cached_listings_data.get('listings', [])
    else:
        # Cache miss - fetch fresh
        listings = get_detailed_proimobil_api_listings()

    if not listings:
        raise HTTPException(status_code=404, detail="No listings available")

    # Get market insights
    from app.services.cache import get_market_cache
    cache = get_market_cache()

    cached_insights = cache.get('market_insights')
    if cached_insights:
        insights = _reconstruct_market_insights(cached_insights)
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


@router.get('/proimobil-api/price-analysis')
async def proimobil_api_price_analysis():
    listings = _get_proimobil_api_listings()
    return _compute_price_analysis(listings)


@router.get('/proimobil-api/deal-scoring')
async def proimobil_api_deal_scoring():
    listings = _get_proimobil_api_listings()
    scoring = _compute_deal_scoring(listings)
    # if you don't want to expose the entire scored_listings, you can remove it from here
    return {
        k: v for k, v in scoring.items()
        if k != 'scored_listings'
    }


@router.get('/proimobil-api/investment-insights')
async def proimobil_api_investment_insights():
    listings = _get_proimobil_api_listings()
    return _compute_investment_insights(listings)


@router.get('/proimobil-api/trends')
async def proimobil_api_trends():
    listings = _get_proimobil_api_listings()
    return _compute_trends(listings, days_back=30)

@router.get('/proimobil-api/analytics')
async def proimobil_api_analytics():
    """
    Summary analytics for Proimobil API:
    - Price analysis (global + by sector)
    - Deal scoring (conversion + best deals)
    - Investment insights (top sectors)
    - Trends (last 30 days)
    - Market Health Score & Stress Index
    - Time-to-sell model (global + per-segment + sample predictions)
    """
    listings = _get_proimobil_api_listings()
    total_listings = len(listings)

    price = _compute_price_analysis(listings)
    deal = _compute_deal_scoring(listings)
    invest = _compute_investment_insights(listings)
    trends = _compute_trends(listings, days_back=30)
    health_and_time = _compute_market_health_and_time_to_sell(
        listings,
        deal.get('scored_listings', []),
    )


    summary = {
        'snapshot': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_listings': total_listings,
        },
        'price_summary': {
            'global': price.get('price_per_sqm_global'),
            'by_sector': price.get('price_per_sqm_by', {}).get('sector', {}),
        },
        'conversion_summary': {
            'by_sector': deal.get('conversion', {}).get('by_sector', {}),
            'by_condition': deal.get('conversion', {}).get('by_condition', {}),
            'by_state': deal.get('conversion', {}).get('by_state', {}),
            'best_deals_sample': deal.get('best_deals', [])[:10],
        },
        'investment_summary': {
            'top_sectors_by_attractiveness': invest.get('top_sectors_by_attractiveness', []),
        },
        'trends_summary': {
            'window_days': trends.get('window_days'),
            # you can filter to the last 7 days if you want
            'created_per_day': trends.get('created_per_day', {}),
            'updated_per_day': trends.get('updated_per_day', {}),
            'price_per_sqm_by_age_bucket': trends.get('price_per_sqm_by_age_bucket', {}),
        },
        'market_health': health_and_time.get('market_health'),
        'time_to_sell_model': health_and_time.get('time_to_sell_model'),
    }

    return summary
