"""
Dependency injection utilities for FastAPI routes.
"""
from functools import lru_cache

from app.core.config import Settings, get_settings


@lru_cache()
def get_settings_cached() -> Settings:
    """
    Cached settings dependency for FastAPI routes.

    Returns:
        Settings: Application settings instance
    """
    return get_settings()


# Future dependencies can be added here:
# def get_db():
#     """Get database session"""
#     pass
#
# def get_current_user():
#     """Get current authenticated user"""
#     pass

