"""Fixtures testów uwierzytelniania."""

from __future__ import annotations

from collections.abc import Iterator

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


@pytest.fixture
def auth_on(monkeypatch: pytest.MonkeyPatch) -> None:
    """Włącza wymóg logowania — domyślnie testy działają bez tokenu."""
    monkeypatch.setattr(settings, "auth_enabled", True)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
