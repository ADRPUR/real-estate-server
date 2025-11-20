# Stub main module after migration to package layout.
# Backward compatibility for tests/imports expecting `import main`.
from pathlib import Path
import sys

# Add src directory to Python path BEFORE any imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from app.main import app, compute_aggregate_market_summary, fetch_all_rates as _pkg_fetch_all_rates, HTML

FETCH_RATES_FUNC = _pkg_fetch_all_rates


def fetch_all_rates(use_cache: bool = True):
    return FETCH_RATES_FUNC(use_cache=use_cache)


__all__ = ["app", "compute_aggregate_market_summary", "fetch_all_rates", "HTML", "FETCH_RATES_FUNC"]

if __name__ == "__main__":
    import uvicorn
    import os
    import logging
    import colorlog

    # Asigurăm că PYTHONPATH include directorul src
    src_dir = str(Path(__file__).parent / "src")
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = f"{src_dir}:{os.environ['PYTHONPATH']}"
    else:
        os.environ["PYTHONPATH"] = src_dir

    # Configure Uvicorn access logger BEFORE starting the server
    # This ensures HTTP request logs are displayed
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s %(levelname)-8s%(reset)s %(cyan)s[%(name)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    uvicorn_access.addHandler(handler)
    uvicorn_access.setLevel(logging.INFO)
    uvicorn_access.propagate = False

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_config=None, access_log=True)
