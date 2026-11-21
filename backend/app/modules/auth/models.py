"""DTO uwierzytelniania — użytkownik, żądanie logowania, sesja.

PIN nie wychodzi poza `service.py`: `User` to widok publiczny, który trafia
do odpowiedzi API i do nagłówka aplikacji.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Urzędnik zalogowany do systemu."""

    model_config = ConfigDict(from_attributes=True)

    initials: str
    name: str
    role: str
    department_id: str | None = None


class LoginRequest(BaseModel):
    initials: str = Field(min_length=2, max_length=4)
    pin: str = Field(min_length=4, max_length=12)


class Session(BaseModel):
    """Wynik logowania — token do nagłówka `Authorization`."""

    token: str
    user: User
    expires_at: datetime
