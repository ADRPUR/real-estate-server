from datetime import datetime
from pathlib import Path
from importlib import import_module
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Fallback HTML (WeasyPrint) or stub
try:
    from weasyprint import HTML as _WeasyHTML  # type: ignore
except Exception:
    class _WeasyHTML:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass
        def write_pdf(self):
            return b"%PDF-STUB%"

# Resolve templates directory (package root -> templates)
PACKAGE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PACKAGE_DIR / 'templates'
templates_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml'])
)

def _html_class():
    """Return HTML class from main (monkeypatched in tests) or fallback."""
    try:
        main_module = import_module('app.main')
        if hasattr(main_module, 'HTML'):
            return getattr(main_module, 'HTML')
    except Exception:
        pass
    return _WeasyHTML


def generate_report_pdf(config: dict) -> bytes:
    from app.domain.calc import calculate  # lazy import to avoid cycles
    result = calculate(config)
    if result.get('error'):
        raise ValueError(result.get('message', 'Calculation error'))
    tpl = templates_env.get_template('report.html')
    html_str = tpl.render(
        config=config,
        r=result,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M')
    )
    HTMLCls = _html_class()
    return HTMLCls(string=html_str, base_url=str(PACKAGE_DIR)).write_pdf()


def generate_sale_summary_pdf(config: dict, amount: float, currency: str) -> bytes:
    from app.domain.calc import calculate_sale_summary  # lazy import
    summary = calculate_sale_summary(config, amount, currency)
    tpl = templates_env.get_template('sale_summary.html')
    html_str = tpl.render(
        config=config,
        summary=summary,
        currency=currency,
        generated_at=datetime.now().strftime('%Y-%m-%d %H:%M')
    )
    HTMLCls = _html_class()
    return HTMLCls(string=html_str, base_url=str(PACKAGE_DIR)).write_pdf()

__all__ = ["generate_report_pdf", "generate_sale_summary_pdf", "templates_env", "TEMPLATES_DIR"]
