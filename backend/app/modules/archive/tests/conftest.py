"""Fixtures testów wyszukiwania archiwalnego (WS3)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from app.adapters.real.archive import VectorArchiveSearch
from app.core import container
from app.main import app

DATA_DIR = Path(__file__).parent / "data"


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
    """Osobna baza SQLite na cache wektorów — nie dotykamy `data/app.db`."""
    db_engine = create_engine(
        f"sqlite:///{tmp_path / 'archive.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def search(engine: Engine) -> VectorArchiveSearch:
    return VectorArchiveSearch(engine=engine)


@pytest.fixture(scope="session")
def eval_queries() -> list[dict[str, Any]]:
    payload = json.loads((DATA_DIR / "queries.json").read_text(encoding="utf-8"))
    return list(payload["queries"])
