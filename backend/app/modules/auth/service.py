"""Logowanie i weryfikacja tokenów sesji.

Token ma postać `inicjały.wygasa.podpis`, gdzie podpis to HMAC-SHA256 z sekretu
aplikacji. Bez zewnętrznej biblioteki JWT — wystarczy standardowa biblioteka,
a format jest czytelny w logach i łatwy do unieważnienia przez zmianę sekretu.

Użytkownicy pochodzą z `fixtures/users.json`. To celowo atrapa katalogu
osobowego: wdrożenie podłącza tu prawdziwy katalog (LDAP, AD) i podmienia
wyłącznie `_records()`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.errors import AppError
from app.core.settings import settings
from app.modules.auth.models import LoginRequest, Session, User


class Unauthorized(AppError):
    """Brak lub nieprawidłowy token sesji."""

    status_code = 401
    code = "unauthorized"


class Forbidden(AppError):
    """Token poprawny, ale sesja wygasła."""

    status_code = 403
    code = "forbidden"


@lru_cache(maxsize=1)
def _random_secret() -> str:
    """Sekret zastępczy — losowy na czas życia procesu.

    Bez stałego `AUTH_SECRET` w `.env` restart unieważnia wszystkie sesje.
    To bezpieczne domyślne zachowanie, ale w demo niewygodne.
    """
    return secrets.token_urlsafe(32)


def _secret() -> str:
    return settings.auth_secret or _random_secret()


def _sign(payload: str) -> str:
    return hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


@lru_cache(maxsize=4)
def _load(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _records() -> list[dict[str, Any]]:
    return _load(settings.fixtures_dir / "users.json")


def _to_user(record: dict[str, Any]) -> User:
    return User(
        initials=record["initials"],
        name=record["name"],
        role=record["role"],
        department_id=record.get("department_id"),
    )


class AuthService:
    """Logowanie po inicjałach i PIN-ie oraz weryfikacja tokenu."""

    def users(self) -> list[User]:
        """Urzędnicy do wyboru na ekranie logowania — bez PIN-ów."""
        return [_to_user(record) for record in _records()]

    def login(self, req: LoginRequest) -> Session:
        record = next(
            (r for r in _records() if r["initials"].upper() == req.initials.upper()),
            None,
        )
        # `compare_digest` na obu gałęziach — brak wczesnego wyjścia zdradzającego,
        # czy inicjały istnieją.
        expected = str(record["pin"]) if record else ""
        if not hmac.compare_digest(expected, req.pin) or record is None:
            raise Unauthorized("Nieprawidłowe inicjały lub PIN.")

        expires_at = datetime.now(UTC) + timedelta(hours=settings.auth_session_hours)
        payload = f"{record['initials']}.{int(expires_at.timestamp())}"
        return Session(
            token=f"{payload}.{_sign(payload)}",
            user=_to_user(record),
            expires_at=expires_at,
        )

    def verify(self, token: str) -> User:
        parts = token.split(".")
        if len(parts) != 3:
            raise Unauthorized("Nieprawidłowy token sesji.")
        initials, expiry, signature = parts
        if not hmac.compare_digest(_sign(f"{initials}.{expiry}"), signature):
            raise Unauthorized("Nieprawidłowy token sesji.")
        try:
            expires_at = datetime.fromtimestamp(int(expiry), tz=UTC)
        except ValueError as exc:
            raise Unauthorized("Nieprawidłowy token sesji.") from exc
        if expires_at < datetime.now(UTC):
            raise Forbidden("Sesja wygasła — zaloguj się ponownie.")
        record = next((r for r in _records() if r["initials"] == initials), None)
        if record is None:
            raise Unauthorized("Nieprawidłowy token sesji.")
        return _to_user(record)
