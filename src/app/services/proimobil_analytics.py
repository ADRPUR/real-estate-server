from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import median
from typing import Iterable, Dict, List

from app.domain.proimobil_models import (
    ProimobilListing,
    TimeOnMarketStats,
    ReservationStats,
    EngagementStats,
    TimeOnMarketByGroup,
    ProimobilAnalytics,
)


def _compute_time_on_market(listings: Iterable[ProimobilListing]) -> TimeOnMarketStats:
    today = datetime.now(timezone.utc)
    days_list: List[int] = [
        max((today - l.created_at).days, 0) for l in listings
    ]

    if not days_list:
        return TimeOnMarketStats(
            avg_days=0, median_days=0, p75_days=0, max_days=0
        )

    days_list.sort()
    n = len(days_list)
    p75_idx = int(0.75 * (n - 1))

    return TimeOnMarketStats(
        avg_days=sum(days_list) / n,
        median_days=float(median(days_list)),
        p75_days=float(days_list[p75_idx]),
        max_days=days_list[-1],
    )


def _compute_time_on_market_by_group(
    listings: Iterable[ProimobilListing],
) -> TimeOnMarketByGroup:
    today = datetime.now(timezone.utc)

    def build_group(key_fn):
        groups: Dict[str, List[int]] = defaultdict(list)
        for l in listings:
            key = key_fn(l)
            if not key:
                continue
            days = max((today - l.created_at).days, 0)
            groups[str(key)].append(days)

        result: Dict[str, TimeOnMarketStats] = {}
        for key, days in groups.items():
            days.sort()
            n = len(days)
            p75_idx = int(0.75 * (n - 1))
            result[key] = TimeOnMarketStats(
                avg_days=sum(days) / n,
                median_days=float(median(days)),
                p75_days=float(days[p75_idx]),
                max_days=days[-1],
            )
        return result

    listings_list = list(listings)  # cso we can iterate multiple times

    return TimeOnMarketByGroup(
        by_sector=build_group(lambda l: l.sector),
        by_state=build_group(lambda l: l.state),
        by_condition=build_group(lambda l: l.condition),
        by_rooms=build_group(lambda l: l.rooms),
    )


def _compute_reservations(listings: Iterable[ProimobilListing]) -> ReservationStats:
    lst = list(listings)
    total_booked = sum(1 for l in lst if l.booked)
    total_sold = sum(1 for l in lst if l.deal)
    avg_orders = sum(l.order for l in lst) / len(lst) if lst else 0.0
    return ReservationStats(
        total_booked=total_booked,
        total_sold=total_sold,
        avg_orders_per_listing=avg_orders,
    )


def _compute_engagement(listings: Iterable[ProimobilListing]) -> EngagementStats:
    lst = list(listings)
    if not lst:
        return EngagementStats(
            avg_views_per_listing=0.0,
            views_per_day_avg=0.0,
        )

    today = datetime.now(timezone.utc)
    total_views = sum(l.views for l in lst)
    avg_views = total_views / len(lst)

    # views / day (normalized by age of the ad)
    views_per_day = []
    for l in lst:
        days = max((today - l.created_at).days, 1)
        views_per_day.append(l.views / days)

    return EngagementStats(
        avg_views_per_listing=avg_views,
        views_per_day_avg=sum(views_per_day) / len(views_per_day),
    )


def compute_proimobil_analytics(
    listings: list[ProimobilListing],
) -> ProimobilAnalytics:
    total = len(listings)
    base_time_stats = _compute_time_on_market(listings)
    group_time_stats = _compute_time_on_market_by_group(listings)
    reservations = _compute_reservations(listings)
    engagement = _compute_engagement(listings)

    hot_ratio = (sum(1 for l in listings if l.is_hot) / total) if total else 0.0
    exclusive_ratio = (
        sum(1 for l in listings if l.is_exclusive) / total
    ) if total else 0.0

    return ProimobilAnalytics(
        total_listings=total,
        time_on_market=base_time_stats,
        reservations=reservations,
        engagement=engagement,
        hot_offers_ratio=hot_ratio,
        exclusive_ratio=exclusive_ratio,
        time_on_market_by_group=group_time_stats,
    )
