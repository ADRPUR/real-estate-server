import logging, re, concurrent.futures, requests, warnings
from statistics import mean, median
from typing import List
from bs4 import BeautifulSoup
from app.domain.market_stats import MarketStats
from app.services.quartile_analysis import calculate_quartiles

# Suppress SSL warnings for self-signed certificates
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)
_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/118 Safari/537.36"})


def _extract_prices_from_html(html: str) -> List[float]:
    soup = BeautifulSoup(html, "html.parser")
    products_div = None
    for d in soup.find_all("div"):
        classes = d.get("class") or []
        if any("products" in c for c in classes):
            products_div = d; break
    if products_div is None:
        return []
    cards = products_div.find_all("div", class_="rs-card")
    prices: List[float] = []
    for card in cards:
        mort_div = card.find("div", class_=lambda c: c and "mortgage" in c)
        if not mort_div: continue
        text = mort_div.get_text(" ", strip=True)
        m = re.search(r"([\d\s]+)\s*€", text) or re.search(r"€\s*([\d\s]+)", text)
        if not m: continue
        digits = "".join(ch for ch in m.group(1) if ch.isdigit())
        if not digits: continue
        try: prices.append(float(digits))
        except ValueError: continue
    return prices

def _detect_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    pag_div = None
    for d in soup.find_all("div"):
        classes = d.get("class") or []
        if "pagination" in classes and "mt-20" in classes:
            pag_div = d; break
    if not pag_div: return 1
    links_wrapper = pag_div.find("div", class_=lambda c: c and "links" in c)
    if not links_wrapper: return 1
    page_nums: List[int] = []
    for a in links_wrapper.find_all("a", class_=lambda c: c and "link" in c):
        txt = (a.get_text() or "").strip();
        if txt.isdigit(): page_nums.append(int(txt))
    return max(page_nums) if page_nums else 1

def fetch_all_prices_accesimobil(base_url: str) -> List[float]:
    resp = _session.get(base_url, timeout=15, verify=False); resp.raise_for_status()
    first_html = resp.text
    total_pages = _detect_total_pages(first_html)
    prices = _extract_prices_from_html(first_html)
    if total_pages > 1:
        def _fetch(page: int) -> tuple[int, str]:
            url = f"{base_url}&page={page}"; r = _session.get(url, timeout=15, verify=False); r.raise_for_status(); return page, r.text
        pages = list(range(2, total_pages + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(pages))) as ex:
            for page, html in ex.map(_fetch, pages): prices.extend(_extract_prices_from_html(html))
    return prices

def compute_stats_for_accesimobil(base_url: str) -> MarketStats:
    prices = fetch_all_prices_accesimobil(base_url)
    if not prices: raise RuntimeError("No price values/m² were found on accesimobil.md")
    prices_sorted = sorted(prices)

    # Calculate quartiles
    quartiles = calculate_quartiles(prices_sorted)

    return MarketStats(
        source="accesimobil.md", url=base_url, total_ads=len(prices_sorted),
        min_price_per_sqm=round(prices_sorted[0], 2), max_price_per_sqm=round(prices_sorted[-1], 2),
        avg_price_per_sqm=round(mean(prices_sorted), 2), median_price_per_sqm=round(median(prices_sorted), 2),
        q1_price_per_sqm=quartiles['q1'],
        q2_price_per_sqm=quartiles['q2'],
        q3_price_per_sqm=quartiles['q3'],
        iqr_price_per_sqm=quartiles['iqr']
    )
