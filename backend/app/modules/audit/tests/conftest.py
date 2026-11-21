"""Fixtures testów dziennika audytu."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from app.adapters.real.audit import SqlAuditLog
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


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    """Osobna baza SQLite na test — nie dotykamy `data/app.db`."""
    db_engine = create_engine(f"sqlite:///{tmp_path / 'audit.db'}", future=True)
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def audit(engine: Engine) -> SqlAuditLog:
    return SqlAuditLog(engine=engine)
