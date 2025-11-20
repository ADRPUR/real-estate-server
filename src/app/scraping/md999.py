"""
999.md Market Scraper using Selenium for dynamic content.

Supports graceful fallback if Selenium is missing or scraper disabled.
"""

import logging
import re
import asyncio
from pathlib import Path
from statistics import mean, median
from typing import List, Optional
from app.domain.market_stats import MarketStats
from app.core.config import get_settings
from app.services.quartile_analysis import calculate_quartiles

logger = logging.getLogger(__name__)



def extract_price_from_text(text: str) -> Optional[float]:
    """Extract price in euros from text like '85 000 €' or '€85,000'."""
    # Remove spaces and commas for easier matching
    normalized = text.replace(" ", "").replace(",", "")

    # Try to match price with € symbol (more specific)
    # Patterns: 85000€ or €85000
    match = re.search(r'€(\d+)|(\d+)€', normalized)
    if match:
        try:
            price_str = match.group(1) or match.group(2)
            return float(price_str)
        except (ValueError, AttributeError):
            pass

    # Fallback: look for numbers near € in original text
    # Pattern: number followed by € (with possible spaces)
    match = re.search(r'([\d\s]+)\s*€', text)
    if match:
        try:
            # Remove spaces from the matched number
            price_str = match.group(1).replace(" ", "")
            return float(price_str)
        except ValueError:
            pass

    # Another fallback: € followed by number
    match = re.search(r'€\s*([\d\s,]+)', text)
    if match:
        try:
            price_str = match.group(1).replace(" ", "").replace(",", "")
            return float(price_str)
        except ValueError:
            pass

    return None


def extract_area_from_text(text: str) -> Optional[float]:
    """Extract area in m² from text like '52 m²' or '52m2'."""
    # Match patterns like: 52 m² or 52m2 or 52 mp
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|mp)', text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None




async def fetch_999md_with_playwright(url: str, max_pages: int = 3) -> List[float]:
    """
    Fetch apartment listings from 999.md using Playwright.
    
    Args:
        url: The base URL to scrape
        max_pages: Maximum number of pages to scrape
        
    Returns:
        List of prices per square meter (€/m²)
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("Playwright not installed. Install: pip install playwright && playwright install chromium")

    # Check for Playwright browser installation
    cache_dir = Path.home() / ".cache" / "ms-playwright"
    if not cache_dir.exists() or not any(p.name.startswith("chromium") for p in cache_dir.iterdir() if p.is_dir()):
        raise RuntimeError("Playwright browsers not installed. Run: playwright install chromium")

    prices: List[float] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            for page_num in range(1, max_pages + 1):
                # Navigate to page
                page_url = url if page_num == 1 else f"{url}&page={page_num}"
                logger.info(f"999.md fetch page {page_num}: {page_url}")

                await page.goto(page_url, wait_until="networkidle", timeout=30000)
                
                # Wait for the content to load - they use class like "AdShort_wrapper__S8kqq"
                try:
                    await page.wait_for_selector('[class*="AdShort_wrapper"]', timeout=10000)
                except Exception:
                    logger.warning(f"No listings found on page {page_num}; stopping.")
                    break

                # Extract all listing cards
                listings = await page.query_selector_all('[class*="AdShort_wrapper"]')
                logger.info(f"Found {len(listings)} listings on page {page_num}")

                for listing in listings:
                    try:
                        # Extract price from the price section - class like "AdShort_price__U_XPT"
                        price_elem = await listing.query_selector('[class*="AdShort_price"]')
                        if not price_elem:
                            continue
                            
                        price_text = await price_elem.inner_text()
                        price = extract_price_from_text(price_text)

                        if price is None:
                            continue
                        
                        # Extract price per sqm from distance section - class like "AdShort_distance__HB83f"
                        # Format: "1 693 €/m²"
                        price_per_sqm_elem = await listing.query_selector('[class*="AdShort_distance"]')
                        if price_per_sqm_elem:
                            distance_text = await price_per_sqm_elem.inner_text()
                            # Extract number from format "1 693 €/m²"
                            match = re.search(r'([\d\s,.]+)\s*€/m', distance_text)
                            if match:
                                price_per_sqm_str = match.group(1).replace(" ", "").replace(",", "")
                                try:
                                    price_per_sqm = float(price_per_sqm_str)
                                    prices.append(price_per_sqm)
                                    logger.debug(f"Extracted: {price}€, {price_per_sqm}€/m²")
                                    continue
                                except ValueError:
                                    pass

                        # If no price per sqm found, try to calculate from title
                        title_elem = await listing.query_selector('[class*="AdShort_title"]')
                        if title_elem:
                            title_text = await title_elem.inner_text()
                            area = extract_area_from_text(title_text)
                            if area and area > 0:
                                prices.append(price / area)
                                logger.debug(f"Calculated: {price}€ / {area}m² = {price / area:.2f}€/m²")
                            else:
                                logger.debug(f"Skipped listing: could not extract area")
                        else:
                            logger.debug(f"Skipped listing: no title element")

                    except Exception as e:
                        logger.debug(f"Listing parse error: {e}")
                        continue
                
                # Check if there are more pages by looking for pagination
                if page_num < max_pages:
                    # Check if next page exists
                    pagination = await page.query_selector('[class*="Pagination_pagination"]')
                    if pagination:
                        next_button = await pagination.query_selector(f'button[data-test-page-value="{page_num + 1}"]')
                        if not next_button:
                            logger.info("No more pages available")
                            break

                # Small delay between pages
                await asyncio.sleep(1)
                
        finally:
            await browser.close()
    
    logger.info(f"Total prices extracted from 999.md: {len(prices)}")
    return prices


def fetch_999md_with_selenium_improved(url: str, max_pages: int = 3) -> List[float]:
    """
    Improved Selenium implementation for 999.md scraping.
    Uses proper selectors and handles Netskope certificate.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        raise RuntimeError(
            "Selenium not installed. Install with: pip install selenium webdriver-manager"
        )
    
    # Configure SSL for webdriver-manager - disable verification
    import os
    import warnings
    cert_path = "/home/adrianp/netskope-ca.pem"

    # Set environment variables for SSL
    if Path(cert_path).exists():
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['SSL_CERT_FILE'] = cert_path
        logger.info(f"Using Netskope certificate: {cert_path}")

    # Suppress SSL warnings from urllib3
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except:
        pass

    # Disable SSL verification for webdriver-manager (it will use requests internally)
    # Patch webdriver-manager's requests to disable SSL verification
    import requests
    original_get = requests.get
    original_request = requests.request

    def patched_get(*args, **kwargs):
        kwargs['verify'] = False
        return original_get(*args, **kwargs)

    def patched_request(*args, **kwargs):
        kwargs['verify'] = False
        return original_request(*args, **kwargs)

    # Temporarily patch requests
    requests.get = patched_get
    requests.request = patched_request

    # Set up Chrome options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--allow-insecure-localhost")
    opts.add_argument("--disable-web-security")
    opts.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


    driver = None
    prices: List[float] = []

    try:
        # Initialize Chrome driver with webdriver-manager (uses patched requests)
        service = Service(ChromeDriverManager().install())

        # Restore original requests functions after ChromeDriver download
        requests.get = original_get
        requests.request = original_request

        driver = webdriver.Chrome(service=service, options=opts)

        for page_num in range(1, max_pages + 1):
            page_url = url if page_num == 1 else f"{url}&page={page_num}"
            logger.info(f"999.md (Selenium) page {page_num}: {page_url}")
            driver.get(page_url)

            # Wait for the ads list container to load
            import time
            time.sleep(3)  # Initial wait for page load

            # Scroll down to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            # Try multiple possible container selectors
            container_selectors = [
                'div[class*="styles_adlist"]',
            ]

            ads_container_found = False
            for selector in container_selectors:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found container with selector: {selector}")
                    ads_container_found = True
                    break
                except:
                    continue

            if not ads_container_found:
                logger.warning(f"No container found on page {page_num}")
                # # Save page source for debugging
                # try:
                #     debug_file = f"/tmp/999md_page{page_num}.html"
                #     with open(debug_file, 'w', encoding='utf-8') as f:
                #         f.write(driver.page_source)
                #     logger.error(f"Page source saved to {debug_file}")
                # except:
                #     pass
                break

            # Try multiple selectors to find ad listings
            listing_selectors = [
                'div[class*="AdShort_wrapper"]',
            ]

            listings = []
            for selector in listing_selectors:
                listings = driver.find_elements(By.CSS_SELECTOR, selector)
                if listings:
                    logger.info(f"Found {len(listings)} listings with selector: {selector}")
                    break

            if not listings:
                logger.warning(f"No ad listings found on page {page_num}")
                # # Save page source for debugging
                # try:
                #     debug_file = f"/tmp/999md_page{page_num}_no_listings.html"
                #     with open(debug_file, 'w', encoding='utf-8') as f:
                #         f.write(driver.page_source)
                #     logger.error(f"Page source saved to {debug_file}")
                # except:
                #     pass
                # break


            for idx, listing in enumerate(listings, 1):
                try:
                    # Method 1: Try AdShort_distance element (direct price per sqm)
                    try:
                        price_per_sqm_elem = listing.find_element(By.CSS_SELECTOR, 'div[class*="AdShort_distance"]')
                        distance_text = price_per_sqm_elem.text.strip()

                        if distance_text and '€/m' in distance_text:
                            match = re.search(r'([\d\s,.]+)\s*€/m', distance_text)
                            if match:
                                price_per_sqm_str = match.group(1).replace(" ", "").replace(",", "")
                                price_per_sqm = float(price_per_sqm_str)
                                prices.append(price_per_sqm)
                                logger.info(f"Listing {idx}: ✅ {price_per_sqm}€/m² (from distance)")
                                continue
                    except:
                        pass

                    # Method 2: Try to find price per sqm anywhere in the listing
                    try:
                        listing_text = listing.text
                        match = re.search(r'([\d\s,.]+)\s*€/m[²2]', listing_text)
                        if match:
                            price_per_sqm_str = match.group(1).replace(" ", "").replace(",", "")
                            price_per_sqm = float(price_per_sqm_str)
                            prices.append(price_per_sqm)
                            logger.info(f"Listing {idx}: ✅ {price_per_sqm}€/m² (from text)")
                            continue
                    except:
                        pass

                    # Method 3: Calculate from total price and area
                    try:
                        # Find price element
                        price_elem = listing.find_element(By.CSS_SELECTOR, '[class*="price"]')
                        price_text = price_elem.text
                        price_match = re.search(r'([\d\s,.]+)\s*€', price_text)

                        if price_match:
                            price = float(price_match.group(1).replace(" ", "").replace(",", ""))

                            # Find area in title or anywhere in listing
                            area_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|mp)', listing.text, re.IGNORECASE)
                            if area_match:
                                area = float(area_match.group(1))
                                if area > 0:
                                    price_per_sqm = price / area
                                    prices.append(price_per_sqm)
                                    logger.info(f"Listing {idx}: ✅ {price_per_sqm:.2f}€/m² (calculated: {price}€/{area}m²)")
                                    continue
                    except:
                        pass

                    logger.debug(f"Listing {idx}: ❌ Could not extract price")

                except Exception as e:
                    logger.debug(f"Listing {idx}: error: {e}")
                    continue

                    # Extract price per sqm from distance section
                    try:
                        price_per_sqm_elem = listing.find_element(By.CSS_SELECTOR, '[class*="AdShort_distance"]')
                        distance_text = price_per_sqm_elem.text
                        logger.debug(f"Listing {idx}: distance_text = '{distance_text}'")

                        # Extract number from format "1 693 €/m²"
                        match = re.search(r'([\d\s,.]+)\s*€/m', distance_text)
                        if match:
                            price_per_sqm_str = match.group(1).replace(" ", "").replace(",", "")
                            try:
                                price_per_sqm = float(price_per_sqm_str)
                                prices.append(price_per_sqm)
                                logger.info(f"Listing {idx}: Extracted {price}���, {price_per_sqm}€/m²")
                                continue
                            except ValueError:
                                pass
                    except Exception as e:
                        logger.debug(f"Listing {idx}: no distance element ({e})")
                        pass

                    # If no price per sqm found, try to calculate from title
                    try:
                        title_elem = listing.find_element(By.CSS_SELECTOR, '[class*="AdShort_title"]')
                        title_text = title_elem.text
                        logger.debug(f"Listing {idx}: title = '{title_text}'")

                        area = extract_area_from_text(title_text)
                        if area and area > 0:
                            price_per_sqm = price / area
                            prices.append(price_per_sqm)
                            logger.info(f"Listing {idx}: Calculated {price}€ / {area}m² = {price_per_sqm:.2f}€/m²")
                        else:
                            logger.debug(f"Listing {idx}: could not extract area from title")
                    except Exception as e:
                        logger.debug(f"Listing {idx}: no title element ({e})")

                except Exception as e:
                    logger.warning(f"Listing {idx} parse error: {e}")
                    continue
            
            # Check if there are more pages
            if page_num < max_pages:
                try:
                    pagination = driver.find_element(By.CSS_SELECTOR, '[class*="Pagination_pagination"]')
                    try:
                        next_button = pagination.find_element(By.CSS_SELECTOR, f'button[data-test-page-value="{page_num + 1}"]')
                    except:
                        logger.info("No more pages available")
                        break
                except:
                    break

            # Small delay between pages
            import time
            time.sleep(1)

    finally:
        # Restore original requests functions (in case of early exit)
        requests.get = original_get
        requests.request = original_request

        if driver:
            driver.quit()

    logger.info(f"Total prices extracted from 999.md: {len(prices)}")
    return prices


def fetch_999md_with_selenium(url: str, max_pages: int = 3) -> List[float]:
    """
    Deprecated: Use fetch_999md_with_selenium_improved instead.
    """
    return fetch_999md_with_selenium_improved(url, max_pages)


async def safe_fetch_999md_prices(base_url: str) -> List[float]:
    settings = get_settings()
    logger.info("Enter safe_fetch_999md_prices")
    if not settings.enable_999md_scraper:
        logger.info("999.md scraping disabled via settings")
        return []
    try:
        # Use Selenium instead of Playwright (better compatibility)
        prices = await asyncio.to_thread(fetch_999md_with_selenium_improved, base_url, max_pages=settings.max_999md_pages)
        logger.info(f"Fetched {len(prices)} prices from 999.md")
        return prices
    except RuntimeError as e:
        logger.warning(f"999.md runtime issue: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"999.md unexpected failure: {e}", exc_info=True)
        return []


async def fetch_all_999md_prices(base_url: str, use_playwright: bool = True) -> List[float]:
    """
    Fetch all apartment prices from 999.md.
    
    Args:
        base_url: URL to scrape
        use_playwright: If True, use Playwright (recommended), else use Selenium
        
    Returns:
        List of prices per square meter
    """
    if use_playwright:
        return await safe_fetch_999md_prices(base_url)

    # Use asyncio.to_thread for synchronous Selenium function
    return await asyncio.to_thread(fetch_999md_with_selenium_improved, base_url)


async def compute_999md_stats(base_url: str) -> MarketStats:
    """Compute market statistics from 999.md listings."""
    prices = await safe_fetch_999md_prices(base_url)

    if not prices:
        return MarketStats(source="999.md", url=base_url, total_ads=0,
                           min_price_per_sqm=0.0, max_price_per_sqm=0.0,
                           avg_price_per_sqm=0.0, median_price_per_sqm=0.0,
                           q1_price_per_sqm=0.0, q2_price_per_sqm=0.0,
                           q3_price_per_sqm=0.0, iqr_price_per_sqm=0.0)

    prices_sorted = sorted(prices)
    
    # Calculate quartiles
    quartiles = calculate_quartiles(prices_sorted)

    return MarketStats(source="999.md", url=base_url, total_ads=len(prices_sorted),
                       min_price_per_sqm=round(min(prices_sorted), 2),
                       max_price_per_sqm=round(max(prices_sorted), 2),
                       avg_price_per_sqm=round(mean(prices_sorted), 2),
                       median_price_per_sqm=round(median(prices_sorted), 2),
                       q1_price_per_sqm=quartiles['q1'],
                       q2_price_per_sqm=quartiles['q2'],
                       q3_price_per_sqm=quartiles['q3'],
                       iqr_price_per_sqm=quartiles['iqr'])


__all__ = [
    "fetch_all_999md_prices",
    "compute_999md_stats",
    "extract_price_from_text",
    "extract_area_from_text",
    "safe_fetch_999md_prices",
]
