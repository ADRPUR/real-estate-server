import datetime as dt
import app.domain.rates_utils as rates_utils

BNM_XML = b"""<ValCurs Date='16.11.2025'><Valute><CharCode>EUR</CharCode><Value>19,6000</Value></Valute></ValCurs>"""
BNR_XML = b"""<DataSet xmlns='http://www.bnr.ro/xsd'><Body><Cube date='2025-11-14'><Rate currency='EUR'>5,0800</Rate></Cube></Body></DataSet>"""

class FakeBook:
    def __init__(self):
        self.sheet = FakeSheet()
    def sheet_by_index(self, idx):
        return self.sheet

class FakeSheet:
    def __init__(self):
        # rows: header, some filler, RON row, sale row
        self._rows = [
            ['x','x','x'],
            ['COD','Minim','Mediu','Maxim'],
            ['Leu roman RON','','',''],
            ['vanzare','','3.9041',''],
        ]
    @property
    def nrows(self):
        return len(self._rows)
    @property
    def ncols(self):
        return max(len(r) for r in self._rows)
    def cell_value(self, r,c):
        try:
            return self._rows[r][c]
        except IndexError:
            return ''

class FakeResp:
    def __init__(self, content, status=200):
        self.content = content
        self.status_code = status
    def raise_for_status(self):
        if self.status_code!=200:
            raise RuntimeError('HTTP error')

class FakeSession:
    def __init__(self):
        self.calls=[]
    def get(self, url, **kwargs):
        self.calls.append(url)
        if 'official_exchange_rates' in url:
            return FakeResp(BNM_XML)
        if 'nbrfxrates.xml' in url:
            return FakeResp(BNR_XML)
        if 'export-medium-rates' in url:
            return FakeResp(b'xlsbytes')
        return FakeResp(b'',404)

def test_fetch_eur_mdl_from_bnm(monkeypatch):
    monkeypatch.setattr(rates_utils, '_get_session', lambda: FakeSession())
    rate,label,fx_date = rates_utils.fetch_eur_mdl_from_bnm()
    assert abs(rate-19.6)<1e-6
    assert 'BNM official' in label


def test_fetch_eur_ron_from_bnr(monkeypatch):
    monkeypatch.setattr(rates_utils, '_get_session', lambda: FakeSession())
    rate,label = rates_utils.fetch_eur_ron_from_bnr()
    assert abs(rate-5.0800)<1e-6
    assert 'BNR official' in label


def test_fetch_ron_mdl_from_bnm_xls(monkeypatch):
    monkeypatch.setattr(rates_utils, '_get_session', lambda: FakeSession())
    monkeypatch.setattr(rates_utils.xlrd, 'open_workbook', lambda file_contents: FakeBook())
    rate,label = rates_utils.fetch_ron_mdl_from_bnm_xls(dt.date(2025,11,14))
    assert abs(rate-3.9041)<1e-6
    assert 'MDL/RON' in label


def test_fetch_all_rates(monkeypatch):
    monkeypatch.setattr(rates_utils, '_get_session', lambda: FakeSession())
    monkeypatch.setattr(rates_utils.xlrd, 'open_workbook', lambda file_contents: FakeBook())
    rates_utils._RATES_CACHE_TS = None
    rates_utils._RATES_CACHE.clear()
    data = rates_utils.fetch_all_rates(use_cache=False)
    assert set(['eur_to_mdl','eur_to_ron','ron_to_mdl']).issubset(data.keys())
    # second call served from cache
    data2 = rates_utils.fetch_all_rates(use_cache=True)
    assert data2 is rates_utils._RATES_CACHE
