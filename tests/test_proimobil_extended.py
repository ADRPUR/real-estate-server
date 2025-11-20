import app.scraping.proimobil as market_proimobil




COMPLEX_HTML = '''
<nav class="Pagination_pagination_x"><ul><li><a>1</a></li><li><a>2</a></li><li><a>3</a></li></ul></nav>
<div class="PropertyListPage_property-list">
<article class="PropertyCard_property-card">
<div class="PropertyCard_property-card__body">
<div class="PropertyCard_property-card__body__title"><h4>150,000 €</h4></div>
<ul><li>a</li><li>b</li><li>45.5 m</li></ul>
</div>
</article>
<article class="PropertyCard_property-card">
<div class="PropertyCard_property-card__body">
<div class="PropertyCard_property-card__body__title"><h4>invalid price</h4></div>
<ul><li>a</li><li>b</li><li>50 m</li></ul>
</div>
</article>
<article class="PropertyCard_property-card">
<div class="PropertyCard_property-card__body">
<div class="PropertyCard_property-card__body__title"><h4>200,000 €</h4></div>
<ul><li>a</li><li>b</li></ul>
</div>
</article>
</div>
'''

def test_proimobil_detect_total_pages():
    total = market_proimobil.detect_total_pages(COMPLEX_HTML)
    assert total == 3

def test_proimobil_extract_with_invalid_entries():
    prices = market_proimobil.extract_prices_from_page(COMPLEX_HTML)
    # Should extract only the first valid one (150000/45.5)
    assert len(prices) == 1
    assert abs(prices[0] - (150000/45.5)) < 0.01

def test_proimobil_no_pagination():
    html = '<div>No pagination here</div>'
    total = market_proimobil.detect_total_pages(html)
    assert total == 1

def test_proimobil_extract_price_helpers():
    assert market_proimobil.extract_price("140,000 €") == 140000.0
    assert market_proimobil.extract_price("invalid") is None
    assert market_proimobil.extract_area("45.5 m²") == 45.5
    assert market_proimobil.extract_area("no area") is None

