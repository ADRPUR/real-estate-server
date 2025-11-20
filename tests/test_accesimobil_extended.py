import app.scraping.accesimobil as market_accesimobil




COMPLEX_ACC_HTML = '''
<div class="container products">
<div class="rs-card"><div class="mortgage info">€1200 / m²</div></div>
<div class="rs-card"><div class="mortgage info">No price</div></div>
<div class="rs-card"><div class="mortgage info">1500 € / m²</div></div>
</div>
<div class="pagination mt-20"><div class="links"><a class="link">1</a><a class="link">2</a><a class="link">3</a></div></div>
'''

def test_accesimobil_detect_total_pages():
    total = market_accesimobil._detect_total_pages(COMPLEX_ACC_HTML)
    assert total == 3

def test_accesimobil_extract_with_invalid():
    prices = market_accesimobil._extract_prices_from_html(COMPLEX_ACC_HTML)
    assert len(prices) == 2
    assert 1200.0 in prices
    assert 1500.0 in prices

def test_accesimobil_no_pagination():
    html = '<div>No pagination</div>'
    total = market_accesimobil._detect_total_pages(html)
    assert total == 1

def test_accesimobil_no_products_div():
    html = '<div class="other">No products</div>'
    prices = market_accesimobil._extract_prices_from_html(html)
    assert prices == []
