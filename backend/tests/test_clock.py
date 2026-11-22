"""Zegar aplikacji — kotwica demo i znaczniki czasu akcji.

Raport z testów wykazał, że przy `DEMO_TODAY=2026-03-16` terminy były
zakotwiczone, ale wpisy historii i audytu nosiły datę prawdziwego zegara
(listopad 2026). Sprawa z marca 2026 dostawała więc wpis z listopada —
w demo wyglądało to na błąd.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from app.core import clock
from app.core.settings import settings


def test_now_uzywa_daty_demo(monkeypatch: pytest.MonkeyPatch) -> None:
    """P10: znacznik akcji ma datę kotwicy, nie prawdziwego zegara."""
    monkeypatch.setattr(settings, "demo_today", date(2026, 3, 16))

    stamp = clock.now()

    assert stamp.date() == date(2026, 3, 16)
    assert stamp.tzinfo is not None


def test_now_zachowuje_godzine_z_prawdziwego_zegara(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Podmieniamy samą datę — godzina zostaje rzeczywista, żeby wpisy się różniły."""
    monkeypatch.setattr(settings, "demo_today", date(2026, 3, 16))

    stamp = clock.now()

    assert stamp.hour == datetime.now(UTC).hour


def test_now_bez_kotwicy_to_prawdziwy_zegar(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "demo_today", None)

    stamp = clock.now()

    assert abs((datetime.now(UTC) - stamp).total_seconds()) < 5


def test_today_uzywa_kotwicy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "demo_today", date(2026, 3, 16))

    assert clock.today() == date(2026, 3, 16)


def test_today_bez_kotwicy_to_prawdziwa_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "demo_today", None)

    assert clock.today() == date.today()
