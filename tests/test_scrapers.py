import app.scraping.accesimobil as market_accesimobil
import app.scraping.proimobil as market_proimobil



PROIMOBIL_HTML_PAGE_1 = '''<nav class="Pagination_pagination"><ul><li><a>1</a></li><li><a>2</a></li></ul></nav>
<div class="PropertyListPage_property-list_xyz">
<article class="PropertyCard_property-card_a"><div class="PropertyCard_property-card__body_b">
<div class="PropertyCard_property-card__body__title_c"><h4>140,000 €</h4></div>
<ul><li>x</li><li>y</li><li>50 m</li></ul>
</div></article>
</div>'''

PROIMOBIL_HTML_PAGE_2 = '''<div class="PropertyListPage_property-list_xyz">
<article class="PropertyCard_property-card_a"><div class="PropertyCard_property-card__body_b">
<div class="PropertyCard_property-card__body__title_c"><h4>160,000 €</h4></div>
<ul><li>x</li><li>y</li><li>40 m</li></ul>
</div></article>
</div>'''

ACCESIMOBIL_HTML_PAGE_1 = '''<div class="foo products"><div class="rs-card"><div class="mortgage">€5 / m², Mortgage X</div></div></div>
<div class="pagination mt-20"><div class="links"><a class="link">1</a><a class="link">2</a></div></div>'''

ACCESIMOBIL_HTML_PAGE_2 = '''<div class="foo products"><div class="rs-card"><div class="mortgage">€6 / m², Mortgage Y</div></div></div>'''


def test_proimobil_extract_prices():
    prices = market_proimobil.extract_prices_from_page(PROIMOBIL_HTML_PAGE_1)
    assert prices == [140000/50]


def test_proimobil_fetch_all(monkeypatch):
    def fake_fetch_html(url: str):
        if 'page=2' in url:
            return PROIMOBIL_HTML_PAGE_2
        return PROIMOBIL_HTML_PAGE_1
    monkeypatch.setattr(market_proimobil, 'fetch_html', fake_fetch_html)
    prices = market_proimobil.fetch_all_proimobil_prices('http://example.com')
    assert len(prices) == 2
    assert round(prices[0],2) == 2800.0
    assert round(prices[1],2) == 4000.0


def test_accesimobil_extract_prices():
    prices = market_accesimobil._extract_prices_from_html(ACCESIMOBIL_HTML_PAGE_1)
    assert prices == [5.0]


def test_accesimobil_fetch_all(monkeypatch):
    def fake_session_get(url, timeout=15, verify=False):
        class R:
            def __init__(self, text):
                self.text = text
            def raise_for_status(self):
                pass
        if 'page=2' in url:
            return R(ACCESIMOBIL_HTML_PAGE_2)
        return R(ACCESIMOBIL_HTML_PAGE_1)
    monkeypatch.setattr(market_accesimobil, '_session', type('S', (), {'get': fake_session_get}))
    prices = market_accesimobil.fetch_all_prices_accesimobil('http://example.com')
    assert prices == [5.0, 6.0]
