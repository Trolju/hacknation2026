"""Testy endpointów archiwum — atrapa i adapter realny."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.real.archive import VectorArchiveSearch
from app.core import container, db


@pytest.fixture
def real_archive(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[VectorArchiveSearch]:
    """Włącza `MODULE_MODE_ARCHIVE=real` i podstawia tymczasową bazę cache."""
    engine: Engine = create_engine(
        f"sqlite:///{tmp_path / 'api.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setenv("MODULE_MODE_ARCHIVE", "real")
    container.reset()

    archive = container.get_archive()
    assert isinstance(archive, VectorArchiveSearch)
    yield archive
    engine.dispose()


def test_default_mode_uses_fake(client: TestClient) -> None:
    assert isinstance(container.get_archive(), FakeArchiveSearch)


def test_similar_returns_ranked_cases(
    client: TestClient, real_archive: VectorArchiveSearch
) -> None:
    response = client.post(
        "/api/archive/similar",
        json={"text": "Ile wynoszą diety wypłacane radnym?", "k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload
    assert payload[0]["archive_id"] == "a0028"
    scores = [item["score"] for item in payload]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)
    assert payload[0]["matched_terms"]
    assert payload[0]["snippet"]
    assert payload[0]["response_excerpt"]


def test_similar_with_empty_text_returns_empty_list(
    client: TestClient, real_archive: VectorArchiveSearch
) -> None:
    response = client.post("/api/archive/similar", json={"text": "", "k": 5})

    assert response.status_code == 200
    assert response.json() == []


def test_similar_without_hits_returns_empty_list(
    client: TestClient, real_archive: VectorArchiveSearch
) -> None:
    response = client.post("/api/archive/similar", json={"text": "xyzzy plugh", "k": 5})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("k", [0, 21])
def test_similar_rejects_k_outside_range(
    client: TestClient, real_archive: VectorArchiveSearch, k: int
) -> None:
    response = client.post("/api/archive/similar", json={"text": "diety radnych", "k": k})

    assert response.status_code == 422


def test_similar_respects_year_from(client: TestClient, real_archive: VectorArchiveSearch) -> None:
    response = client.post(
        "/api/archive/similar",
        json={"text": "diety wypłacane radnym", "k": 5, "year_from": 2026},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_returns_case(client: TestClient, real_archive: VectorArchiveSearch) -> None:
    response = client.get("/api/archive/a0001")

    assert response.status_code == 200
    payload = response.json()
    assert payload["archive_id"] == "a0001"
    assert payload["case_number"] == "BKS.IV.1431.87.2025"
    assert payload["request_text"]
    assert payload["response_text"]
    assert payload["departments"]


def test_get_unknown_returns_not_found(
    client: TestClient, real_archive: VectorArchiveSearch
) -> None:
    response = client.get("/api/archive/a9999")

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["message"] == "Nie znaleziono sprawy archiwalnej."


def test_fake_mode_serves_similar(client: TestClient) -> None:
    response = client.post("/api/archive/similar", json={"text": "diety radnych", "k": 3})

    assert response.status_code == 200
    assert response.json()
