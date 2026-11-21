"""Fixtures testów modułu routingu.

Moduł ma własny `conftest.py`, bo testy w `app/modules/*/tests/` nie widzą
`backend/tests/conftest.py`. Kontener czyścimy przed i po każdym teście, żeby
przełączanie `MODULE_MODE_ROUTING` nie przeciekało między testami.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core import container
from app.main import app


@pytest.fixture(autouse=True)
def _reset_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
