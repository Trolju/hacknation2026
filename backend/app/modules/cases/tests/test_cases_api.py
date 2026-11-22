"""API wniosków: kontener wybiera `SqlCaseRepository`, router deleguje do serwisu."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine

from app.adapters.fakes.cases import FakeCaseRepository
from app.adapters.real.cases import SqlCaseRepository
from app.core import container
from app.main import app


@pytest.fixture
def real_client(sql_engine: Engine) -> Iterator[TestClient]:
    """Klient API z repozytorium SQL na tymczasowej bazie."""
    repo = SqlCaseRepository(engine=sql_engine)
    app.dependency_overrides[container.get_cases] = lambda: repo
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_container_resolves_sql_repository(
    monkeypatch: pytest.MonkeyPatch, sql_engine: Engine
) -> None:
    monkeypatch.setenv("MODULE_MODE_CASES", "real")
    monkeypatch.setattr("app.adapters.real.cases.default_engine", sql_engine)
    container.reset()
    assert isinstance(container.get_cases(), SqlCaseRepository)


def test_container_falls_back_to_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODULE_MODE_CASES", "fake")
    container.reset()
    assert isinstance(container.get_cases(), FakeCaseRepository)


def test_list_uses_real_repository(real_client: TestClient) -> None:
    rows = real_client.get("/api/cases").json()
    assert len(rows) == 10
    assert rows[0]["urgency"] in {"overdue", "today", "tomorrow", "soon", "normal", "closed"}


def test_transition_refreshes_list(real_client: TestClient) -> None:
    case_id = real_client.get("/api/cases", params={"status": "nowy"}).json()[0]["id"]
    response = real_client.post(
        f"/api/cases/{case_id}/transition", json={"to": "zapytania_wyslane"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "zapytania_wyslane"
    rows = real_client.get("/api/cases", params={"status": "zapytania_wyslane"}).json()
    assert case_id in {row["id"] for row in rows}


def test_transition_without_note_returns_409(real_client: TestClient) -> None:
    case_id = real_client.get("/api/cases", params={"status": "nowy"}).json()[0]["id"]
    real_client.post(f"/api/cases/{case_id}/transition", json={"to": "zapytania_wyslane"})
    response = real_client.post(f"/api/cases/{case_id}/transition", json={"to": "nowy"})
    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "invalid_transition"
    assert body["details"]["reason"] == "note_required"
    assert "notatki" in body["message"]


def test_transition_with_note_succeeds(real_client: TestClient) -> None:
    case_id = real_client.get("/api/cases", params={"status": "nowy"}).json()[0]["id"]
    real_client.post(f"/api/cases/{case_id}/transition", json={"to": "zapytania_wyslane"})
    response = real_client.post(
        f"/api/cases/{case_id}/transition",
        json={"to": "nowy", "note": "Wysłano przez pomyłkę"},
    )
    assert response.status_code == 200
    history = real_client.get(f"/api/cases/{case_id}/history").json()
    assert history[-1]["note"] == "Wysłano przez pomyłkę"


def test_create_with_too_long_subject_returns_422(real_client: TestClient) -> None:
    response = real_client.post(
        "/api/cases",
        json={
            "case_number": "BKS.IV.1431.95.2026",
            "subject": "x" * 201,
            "inflow_date": "2026-03-16",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_failed"


def test_duplicate_case_number_returns_409(real_client: TestClient) -> None:
    response = real_client.post(
        "/api/cases",
        json={
            "case_number": "BKS.IV.1431.1.2026",
            "subject": "Duplikat numeru",
            "inflow_date": "2026-03-16",
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
