# Package main entrypoint (updated after cleanup of legacy modules)
from __future__ import annotations
import logging, threading, asyncio, statistics as stats_mod
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape
import colorlog
from contextlib import asynccontextmanager
# Add safe HTML import (WeasyPrint) for PDF tests monkeypatch compatibility
try:
    from weasyprint import HTML  # type: ignore
except Exception:  # fallback stub
    class HTML:  # minimal stub
        def __init__(self, *args, **kwargs):
            pass
        def write_pdf(self):
            return b"%PDF-STUB%"
from app.core.config import get_settings
from app.domain.market_stats import MarketStats
# Updated imports from scraping layer
from app.scraping.proimobil import (
    compute_proimobil_stats,
    fetch_all_proimobil_prices,
)
from app.scraping.accesimobil import (
    compute_stats_for_accesimobil,
    fetch_all_prices_accesimobil,
)
from app.scraping.md999 import (
    compute_999md_stats,
    fetch_all_999md_prices,
)
from app.services.histogram import get_price_distribution_summary
from app.services.quartile_analysis import calculate_quartiles, remove_outliers_iqr

# Routers (ensure these exist in api/ directory)
from app.api.v1.routes_pdf import router as pdf_router
from app.api.v1.routes_rates import router as rates_router
from app.api.v1.routes_market import router as market_router
from app.api.v1.routes_misc import router as misc_router
from app.api.v1.routes_cache import router as cache_router
from app.services.rates import fetch_all_rates as _rates_fetch

settings = get_settings()

# Logging configuration
_handler = colorlog.StreamHandler()
_handler.setFormatter(colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(cyan)s[%(name)s]%(reset)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
_root_logger = logging.getLogger()
if not _root_logger.handlers:
    _root_logger.addHandler(_handler)
_root_logger.setLevel(settings.log_level.upper())
for noisy in ["fontTools", "fontTools.subset", "fontTools.ttLib", "weasyprint", "urllib3"]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

# Configure Uvicorn loggers to match app format
# Apply the same colored formatter to uvicorn loggers
for uvicorn_logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.handlers.clear()
    uvicorn_handler = colorlog.StreamHandler()
    uvicorn_handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(cyan)s[%(name)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    uvicorn_logger.addHandler(uvicorn_handler)
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.propagate = False

logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize cache and scheduler on startup, cleanup on shutdown."""
    logger.info("=" * 60)
    logger.info("Starting Apartment Calculator API...")
    logger.info("=" * 60)

    # Initialize cache and scheduler
    from app.services.cache import init_cache_and_scheduler, get_market_scheduler
    init_cache_and_scheduler()

    logger.info("API startup complete!")
    logger.info("=" * 60)

    yield  # Application is running

    # Cleanup on shutdown
    logger.info("Shutting down...")
    scheduler = get_market_scheduler()
    scheduler.stop()
    logger.info("Scheduler stopped. Goodbye!")

# FastAPI app
app = FastAPI(title="Apartment Calculator API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# Templates (used by pdf service)
PACKAGE_DIR = Path(__file__).parent
TEMPLATES_DIR = PACKAGE_DIR / "templates"
templates_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def _fmt_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return value
templates_env.filters["fmt_date"] = _fmt_date

# Caching for aggregated market summary
MARKET_SUMMARY_TTL = timedelta(minutes=settings.market_summary_ttl_minutes)
_market_summary_cache = None
_market_summary_cache_ts = None
_market_summary_lock = threading.Lock()

# Wrapper preserved for tests monkeypatch compatibility

def fetch_all_rates(use_cache: bool = True):
    return _rates_fetch(use_cache=use_cache)

# Routers
app.include_router(pdf_router)
app.include_router(rates_router)
app.include_router(market_router)
app.include_router(misc_router)
app.include_router(cache_router)

# Aggregate market summary computation (kept for test patching)

async def compute_aggregate_market_summary() -> dict:
    """
    Compute aggregate market summary from all sources.

    Note: This function is now async to support 999.md Playwright scraping.

    Returns a dict with:
    - sources: list of MarketStats for each source
    - quartile_analysis: overall market quartile analysis
    """
    # Fetch stats from all sources (999.md is async, others are sync)
    pro_stats = compute_proimobil_stats(settings.proimobil_url)
    acc_stats = compute_stats_for_accesimobil(settings.accesimobil_url)
    md999_stats = await compute_999md_stats(settings.md999_url)

    # Fetch all prices for distribution (reuse from stats to avoid double scraping)
    all_prices: list[float] = []
    all_prices.extend(fetch_all_proimobil_prices(settings.proimobil_url))
    all_prices.extend(fetch_all_prices_accesimobil(settings.accesimobil_url))
    all_prices.extend(await fetch_all_999md_prices(settings.md999_url))

    if not all_prices:
        raise RuntimeError("No prices collected")

    # Compute distribution for all combined prices
    dist = get_price_distribution_summary(all_prices)

    # Calculate quartiles for aggregate
    quartiles = calculate_quartiles(all_prices)

    # Detect outliers
    _, num_outliers = remove_outliers_iqr(all_prices)

    # Create aggregate stats
    all_stats = MarketStats(
        source="all", url=None, total_ads=len(all_prices),
        min_price_per_sqm=round(min(all_prices), 2),
        max_price_per_sqm=round(max(all_prices), 2),
        avg_price_per_sqm=round(stats_mod.mean(all_prices), 2),
        median_price_per_sqm=round(stats_mod.median(all_prices), 2),
        price_histogram=dist["histogram"],
        dominant_range=dist["dominant_range"],
        dominant_percentage=dist["dominant_percentage"],
        q1_price_per_sqm=quartiles['q1'],
        q2_price_per_sqm=quartiles['q2'],
        q3_price_per_sqm=quartiles['q3'],
        iqr_price_per_sqm=quartiles['iqr']
    )

    # Build quartile analysis summary (in English)
    q1 = quartiles['q1']
    q2 = quartiles['q2']
    q3 = quartiles['q3']
    iqr = quartiles['iqr']

    quartile_analysis = {
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "iqr": iqr,
        "total_ads": len(all_prices),
        "outliers_removed": num_outliers,
        "outliers_percentage": round((num_outliers / len(all_prices)) * 100, 2) if all_prices else 0,
        "interpretation": {
            "market_width": "narrow" if iqr < 300 else "moderate" if iqr < 600 else "wide",
            "price_range_description": f"Most prices are between {q1:.0f} €/m² (Q1) and {q3:.0f} €/m² (Q3)",
            "iqr_description": f"The central price distribution has a width of {iqr:.0f} €/m²",
            "budget_range": f"< {q1:.0f} €/m²",
            "affordable_range": f"{q1:.0f} - {q2:.0f} €/m²",
            "mid_range": f"{q2:.0f} - {q3:.0f} €/m²",
            "premium_range": f"> {q3:.0f} €/m²",
        },
        "sources_breakdown": {
            "proimobil": pro_stats.total_ads,
            "accesimobil": acc_stats.total_ads,
            "999md": md999_stats.total_ads
        }
    }

    return {
        "sources": [pro_stats, acc_stats, md999_stats, all_stats],
        "quartile_analysis": quartile_analysis
    }

@app.get("/market/summary")
async def market_summary():
    """
    Get aggregate market summary from all sources (proimobil, accesimobil, 999.md).

    Note: This endpoint may take 15-30 seconds due to 999.md Playwright scraping.
    Results are cached for 30 minutes.
    """
    global _market_summary_cache, _market_summary_cache_ts
    now = datetime.now(timezone.utc)
    with _market_summary_lock:
        if _market_summary_cache and _market_summary_cache_ts and (now - _market_summary_cache_ts < MARKET_SUMMARY_TTL):
            return _market_summary_cache

    # Call async function directly (no asyncio.to_thread needed)
    stats_list = await compute_aggregate_market_summary()

    with _market_summary_lock:
        _market_summary_cache = stats_list
        _market_summary_cache_ts = now
    return stats_list

__all__ = ["app", "fetch_all_rates", "compute_aggregate_market_summary", "TEMPLATES_DIR", "templates_env", "HTML"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
