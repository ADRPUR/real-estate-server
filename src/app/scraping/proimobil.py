import logging, re, requests, concurrent.futures, warnings
from statistics import mean, median
from typing import List, Optional
from bs4 import BeautifulSoup
from app.domain.market_stats import MarketStats
from app.services.quartile_analysis import calculate_quartiles

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)
PRICE_RE = re.compile(r"([\d.,]+)")
AREA_RE = re.compile(r"([\d.,]+)\s*m")

session = requests.Session(); session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/118 Safari/537.36"})


def extract_price(text: str) -> Optional[float]:
    m = PRICE_RE.search(text.replace(" ", ""))
    if not m: return None
    try: return float(m.group(1).replace(",", ""))
    except Exception: return None

def extract_area(text: str) -> Optional[float]:
    m = AREA_RE.search(text.replace(" ", ""))
    if not m: return None
    try: return float(m.group(1).replace(",", "."))
    except Exception: return None

def fetch_html(url: str) -> str:
    r = session.get(url, timeout=15, verify=False); r.raise_for_status(); return r.text

def detect_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    nav = soup.find("nav", class_=lambda c: c and "Pagination_pagination" in c)
    if not nav: return 1
    last_number = 1
    for a in nav.select("ul li a"):
        txt = (a.text or "").strip()
        if txt.isdigit(): last_number = max(last_number, int(txt))
    return last_number

def extract_prices_from_page(html: str) -> List[float]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_=lambda c: c and "PropertyListPage_property-list" in c)
    if not root: return []
    cards = root.find_all("article", class_=lambda c: c and "PropertyCard_property-card" in c)
    results: List[float] = []
    for card in cards:
        body = card.find("div", class_=lambda c: c and "PropertyCard_property-card__body" in c)
        if not body: continue
        title_div = body.find("div", class_=lambda c: c and "PropertyCard_property-card__body__title" in c)
        if not title_div: continue
        h4 = title_div.find("h4")
        if not h4: continue
        price = extract_price(h4.text)
        if price is None: continue
        ul = body.find("ul")
        if not ul: continue
        lis = ul.find_all("li")
        if len(lis) < 3: continue
        area = extract_area(lis[2].text)
        if area is None or area <= 0: continue
        results.append(price / area)
    return results

def fetch_all_proimobil_prices(base_url: str) -> List[float]:
    html = fetch_html(base_url); total_pages = detect_total_pages(html)
    all_prices: List[float] = []
    all_prices.extend(extract_prices_from_page(html))
    if total_pages > 1:
        def _fetch(page: int) -> tuple[int, str]:
            url = f"{base_url}&page={page}"; h = fetch_html(url); return page, h
        pages = list(range(2, total_pages + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(pages))) as ex:
            for page, html_page in ex.map(_fetch, pages): all_prices.extend(extract_prices_from_page(html_page))
    return all_prices

def compute_proimobil_stats(base_url: str) -> MarketStats:
    prices = fetch_all_proimobil_prices(base_url)
    if not prices: raise RuntimeError("No price values/m² were found on proimobil.md")

    # Calculate quartiles
    quartiles = calculate_quartiles(prices)

    return MarketStats(
        source="proimobil.md", url=base_url, total_ads=len(prices),
        min_price_per_sqm=round(min(prices), 2), max_price_per_sqm=round(max(prices), 2),
        avg_price_per_sqm=round(mean(prices), 2), median_price_per_sqm=round(median(prices), 2),
        q1_price_per_sqm=quartiles['q1'],
        q2_price_per_sqm=quartiles['q2'],
        q3_price_per_sqm=quartiles['q3'],
        iqr_price_per_sqm=quartiles['iqr']
    )

__all__ = [
    "extract_price", "extract_area", "fetch_html", "detect_total_pages", "extract_prices_from_page",
    "fetch_all_proimobil_prices", "compute_proimobil_stats"
]
