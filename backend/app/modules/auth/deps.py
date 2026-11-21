"""Zależność FastAPI: zalogowany urzędnik.

Tożsamość bierze się z tokenu, nie z pola formularza — dzięki temu
`handler_initials` nie da się podrobić, wpisując cudze inicjały.
"""

from __future__ import annotations

from fastapi import Header

from app.core.settings import settings
from app.modules.auth.models import User
from app.modules.auth.service import AuthService, Unauthorized


def current_user(authorization: str | None = Header(default=None)) -> User:
    """Urzędnik z nagłówka `Authorization: Bearer <token>`.

    Przy `AUTH_ENABLED=false` zwraca pierwszego użytkownika z fixtures. Dzięki
    temu testy i pokazy bez logowania działają, ale inicjały w sprawie nadal
    pochodzą z tożsamości, a nie z pola w formularzu.
    """
    service = AuthService()
    if not settings.auth_enabled:
        users = service.users()
        if not users:
            raise Unauthorized("Brak skonfigurowanych użytkowników.")
        return users[0]
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthorized("Wymagane zalogowanie.")
    return service.verify(authorization.split(" ", 1)[1].strip())
