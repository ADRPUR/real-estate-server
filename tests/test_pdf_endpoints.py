from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module

# Minimal config for PDF endpoints
CONFIG = {
    "new_apartment": {"price_apartment": 50000},
    "old_apartment": {"purchase_price": 40000},
    "exchange_rates": {"eur_to_mdl": 19.5, "eur_to_ron": 4.95, "ron_to_mdl": 3.94},
    "agent_fee": {"enabled": False, "percentage": 0},
    "income_tax": {"enabled": False, "rate": 0},
    "notary_tax": {"enabled": False, "percentage": 0},
    "rental_income": {"enabled": False},
}

class DummyHTML:
    def __init__(self, *args, **kwargs):
        pass
    def write_pdf(self):
        return b'%PDF-FAKE%'

def test_pdf_generation(monkeypatch):
    monkeypatch.setattr(main_module, 'HTML', DummyHTML)
    client = TestClient(app)
    resp = client.post('/pdf', json={'config': CONFIG})
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')

def test_pdf_sale_summary_generation(monkeypatch):
    monkeypatch.setattr(main_module, 'HTML', DummyHTML)
    client = TestClient(app)
    resp = client.post('/pdf/sale-summary', json={'config': CONFIG, 'amount': 100000, 'currency': 'EUR'})
    assert resp.status_code == 200
    assert resp.content.startswith(b'%PDF')

def test_pdf_generation_error(monkeypatch):
    """Test PDF generation with calculation error."""
    bad_config = {
        "new_apartment": {"price_apartment": 10000},
        "old_apartment": {"purchase_price": 5000},
        "exchange_rates": {"eur_to_mdl": 10, "eur_to_ron": 2, "ron_to_mdl": 20},
        "agent_fee": {"enabled": True, "percentage": 50},
        "income_tax": {"enabled": True, "rate": 50},
        "currency_conversion": {"enabled": True},
    }
    client = TestClient(app)
    resp = client.post('/pdf', json={'config': bad_config})
    assert resp.status_code == 400
    assert b"denom" in resp.content or b"Coefficients" in resp.content


def test_pdf_sale_summary_error():
    """Test sale summary with invalid currency conversion."""
    bad_config = {
        "old_apartment": {"purchase_price": 10000},
        "exchange_rates": {"eur_to_mdl": 0},
        "agent_fee": {"enabled": False},
        "income_tax": {"enabled": False},
    }
    client = TestClient(app)
    resp = client.post('/pdf/sale-summary', json={'config': bad_config, 'amount': 100000, 'currency': 'MDL'})
    assert resp.status_code == 400
