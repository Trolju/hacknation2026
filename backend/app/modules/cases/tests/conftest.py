"""Wspólne fixtures testów wniosków.

Ten sam zestaw testów uruchamiamy na obu adapterach: atrapie z `fixtures/`
i repozytorium SQL na tymczasowej bazie SQLite. Dzięki temu maszyna stanów,
filtry i sortowanie muszą zachowywać się identycznie w obu implementacjach.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.adapters.fakes.cases import FakeCaseRepository
from app.adapters.real.cases import SqlCaseRepository
from app.core import container
from app.modules.cases.service import CaseService
from app.ports.cases import CaseRepositoryPort


@pytest.fixture(autouse=True)
def _clean_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def sql_engine(tmp_path: Path) -> Iterator[Engine]:
    """Pusta baza SQLite — schemat tworzy adapter przy konstrukcji."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'cases.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(params=["fake", "real"])
def repo(request: pytest.FixtureRequest, sql_engine: Engine) -> CaseRepositoryPort:
    if request.param == "fake":
        return FakeCaseRepository()
    return SqlCaseRepository(engine=sql_engine)


@pytest.fixture
def real_repo(sql_engine: Engine) -> SqlCaseRepository:
    return SqlCaseRepository(engine=sql_engine)


@pytest.fixture
def service(repo: CaseRepositoryPort) -> CaseService:
    return CaseService(repo)
