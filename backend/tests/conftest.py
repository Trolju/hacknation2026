"""Wspólne fixtures testów backendu."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core import container
from app.main import app


@pytest.fixture(autouse=True)
def _reset_container() -> None:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
