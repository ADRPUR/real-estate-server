"""
FastAPI dependency injection utilities.
"""
from functools import lru_cache
from app.core.config import Settings


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    This is a FastAPI dependency that can be injected into endpoints.
    """
    return Settings()

