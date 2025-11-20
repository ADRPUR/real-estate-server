"""Security stubs: future auth/JWT/session handling.
Currently unused; placeholder for expansion.
"""
from typing import Optional

class AuthService:
    def __init__(self):
        self._enabled = False

    def is_enabled(self) -> bool:
        return self._enabled

    def authenticate(self, token: str) -> Optional[dict]:
        # Placeholder authentication logic
        if not self._enabled:
            return {"anonymous": True}
        return None

auth_service = AuthService()

__all__ = ["auth_service", "AuthService"]

