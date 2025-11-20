import unicodedata, xml.etree.ElementTree as ET, xlrd, requests, logging, threading
from datetime import date
import datetime as _dt
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter, Retry

BNM_XML_URL = "https://www.bnm.md/en/official_exchange_rates"
BNR_XML_URL = "https://www.bnr.ro/nbrfxrates.xml"
BNM_XLS_URL = "https://www.bnm.md/ro/export-medium-rates"
logger = logging.getLogger(__name__)
_session_lock = threading.Lock()
_session: Optional[requests.Session] = None

def _get_session() -> requests.Session:
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                s = requests.Session()
                retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429,500,502,503,504], allowed_methods=["GET"])
                adapter = HTTPAdapter(max_retries=retries)
                s.mount("https://", adapter); s.mount("http://", adapter)
                _session = s
    return _session
_RATES_CACHE: Dict[str, Any] = {}
_RATES_CACHE_TS: Optional[_dt.datetime] = None
_RATES_CACHE_TTL_SECONDS = 1800

def _cache_valid() -> bool:
    if _RATES_CACHE_TS is None: return False
    age = (_dt.datetime.now(_dt.timezone.utc) - _RATES_CACHE_TS).total_seconds()
    return age < _RATES_CACHE_TTL_SECONDS

def _norm(s: str) -> str:
    if not isinstance(s, str): s = str(s)
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()

def fetch_eur_mdl_from_bnm(session: Optional[requests.Session] = None) -> tuple[float,str,_dt.date]:
    if session is None: session = _get_session()
    today_date = date.today(); today_str = today_date.strftime("%d.%m.%Y")
    resp = session.get(BNM_XML_URL, params={"get_xml":"1","date":today_str}, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content); valcurs_date = root.attrib.get("Date", today_str)
    eur_value = None
    for val in root.findall("Valute"):
        if val.findtext("CharCode") == "EUR":
            raw = val.findtext("Value") or ""; eur_value = float(raw.replace(",",".")); break
    if eur_value is None: raise RuntimeError("EUR not found in BNM XML")
    try: fx_date = _dt.datetime.strptime(valcurs_date, "%d.%m.%Y").date()
    except ValueError: fx_date = today_date
    label = f"BNM official EUR/MDL (XML, {valcurs_date})"
    return eur_value,label,fx_date

def fetch_eur_ron_from_bnr(session: Optional[requests.Session] = None) -> tuple[float,str]:
    if session is None: session = _get_session()
    resp = session.get(BNR_XML_URL, timeout=10); resp.raise_for_status()
    root = ET.fromstring(resp.content)
    ns_uri = root.tag.split("}")[0].strip("{") if root.tag.startswith("{") else "http://www.bnr.ro/xsd"
    ns = {"bnr": ns_uri}
    cube = root.find(".//bnr:Body/bnr:Cube", ns) or root.find(".//bnr:Cube", ns)
    if cube is None: raise RuntimeError("No Cube element in BNR XML")
    date_str = cube.attrib.get("date", "") or cube.attrib.get("Date", "")
    if date_str:
        try:
            if "-" in date_str: date_str = _dt.datetime.strptime(date_str, "%Y-%m-%d").date().strftime("%d.%m.%Y")
            else: _dt.datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError: pass
    eur_rate = None
    for rate in cube.findall("bnr:Rate", ns):
        if rate.attrib.get("currency") == "EUR":
            eur_rate = float((rate.text or "0").replace(",",".")); break
    if eur_rate is None: raise RuntimeError("EUR not found in BNR XML")
    label = f"BNR official EUR/RON (XML, {date_str})"
    return eur_rate,label

def fetch_ron_mdl_from_bnm_xls(target_date: Optional[_dt.date] = None, session: Optional[requests.Session] = None) -> tuple[float,str]:
    if session is None: session = _get_session()
    if target_date is None: target_date = _dt.date.today()
    if target_date.weekday() >= 5: target_date -= _dt.timedelta(days=target_date.weekday() - 4)
    date_str = target_date.strftime("%d.%m.%Y")
    resp = session.get(BNM_XLS_URL, params={"date":date_str,"xls":"1"}, timeout=10); resp.raise_for_status()
    book = xlrd.open_workbook(file_contents=resp.content); sheet = book.sheet_by_index(0)
    header_row = code_col = medium_col = None
    for rowx in range(sheet.nrows):
        row = [_norm(sheet.cell_value(rowx, colx)) for colx in range(sheet.ncols)]
        if "minim" in row and ("mediu" in row or "medium" in row):
            header_row = rowx; code_col = row.index(next(c for c in row if "minim" in c)) - 1; medium_col = row.index(next(c for c in row if "mediu" in c or "medium" in c)); break
    if header_row is None: raise RuntimeError("Header with Minim / Mediu not found in XLS")
    ron_row = None
    for rowx in range(header_row + 1, sheet.nrows):
        txt = _norm(sheet.cell_value(rowx, 0))
        if all(k in txt for k in ["ron","leu","roman"]): ron_row = rowx; break
    if ron_row is None: raise RuntimeError("Could not find RON row in BNM XLS")
    sale_row = None
    for rowx in range(ron_row + 1, ron_row + 4):
        if rowx >= sheet.nrows: break
        row = _norm(sheet.cell_value(rowx, 0))
        if "vanzare" in row: sale_row = rowx; break
    if sale_row is None: raise RuntimeError("RON block found, but 'Vânzare' row missing")
    try: rate = float(sheet.cell_value(sale_row, medium_col))
    except Exception: raise RuntimeError("Could not extract medium rate for RON from XLS")
    label = f"BNM medium MDL/RON (XLS, {date_str})"
    return rate,label

def fetch_all_rates(use_cache: bool = True) -> Dict[str, Any]:
    if use_cache and _cache_valid(): return _RATES_CACHE
    session = _get_session()
    eur_to_mdl, bnm_label, fx_date = fetch_eur_mdl_from_bnm(session)
    eur_to_ron, bnr_label = fetch_eur_ron_from_bnr(session)
    try:
        ron_to_mdl, ron_label = fetch_ron_mdl_from_bnm_xls(fx_date, session)
    except Exception:
        ron_to_mdl = eur_to_mdl / eur_to_ron
        ron_label = f"Cross-rate MDL/RON din {bnm_label} și {bnr_label}"
    data = {
        "date": fx_date.isoformat(),
        "eur_to_mdl": eur_to_mdl,
        "eur_to_mdl_label": bnm_label,
        "eur_to_ron": eur_to_ron,
        "eur_to_ron_label": bnr_label,
        "ron_to_mdl": ron_to_mdl,
        "ron_to_mdl_label": ron_label,
    }
    global _RATES_CACHE_TS; _RATES_CACHE_TS = _dt.datetime.now(_dt.timezone.utc)
    _RATES_CACHE.clear(); _RATES_CACHE.update(data)
    return data

__all__ = ["fetch_all_rates", "fetch_eur_mdl_from_bnm", "fetch_eur_ron_from_bnr", "fetch_ron_mdl_from_bnm_xls", "_get_session", "_RATES_CACHE", "_RATES_CACHE_TS", "xlrd"]
