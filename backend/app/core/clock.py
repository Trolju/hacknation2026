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
    """Znacznik czasu akcji — wpisy historii, audytu i wersji projektu.

    W trybie demo data jest zakotwiczona na `demo_today`, a godzina bierze się
    z prawdziwego zegara. Bez tego sprawa z marca 2026 dostawała wpis z datą
    listopada 2026 i w demo wyglądało to na błąd.
    """
    current = datetime.now(UTC)
    anchor = settings.demo_today
    if anchor is None:
        return current
    return current.replace(year=anchor.year, month=anchor.month, day=anchor.day)


def days_between(start: date, end: date) -> int:
    return (end - start).days
