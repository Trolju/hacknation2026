"""Zegar aplikacji.

W trybie demo "dziś" jest zakotwiczone na `settings.demo_today`, żeby fixtures
zawsze pokazywały właściwe kolory terminów. W produkcji `demo_today=None`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.settings import settings


def today() -> date:
    return settings.demo_today or date.today()


def now() -> datetime:
    return datetime.now(UTC)


def days_between(start: date, end: date) -> int:
    return (end - start).days
