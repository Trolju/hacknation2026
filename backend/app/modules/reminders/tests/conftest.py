"""Fixtures testów przypomnień o terminach (W11)."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core import container
from app.core.settings import settings
from app.main import app


@pytest.fixture(autouse=True)
def _reset_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture(autouse=True)
def _demo_today(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kotwica czasu demo — testy opisują konkretne terminy z `fixtures/`."""
    monkeypatch.setattr(settings, "demo_today", date(2026, 3, 16))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
