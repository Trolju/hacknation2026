"""Testy endpointu `GET /api/audit` — atrapa i adapter realny."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from app.adapters.fakes.audit import FakeAuditLog
from app.adapters.real.audit import SqlAuditLog
from app.core import container, db
from app.main import app


@pytest.fixture
def real_audit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[SqlAuditLog]:
    """Włącza `MODULE_MODE_AUDIT=real` i podstawia tymczasową bazę."""
    engine: Engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}", future=True)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setenv("MODULE_MODE_AUDIT", "real")
    container.reset()

    audit = container.get_audit()
    assert isinstance(audit, SqlAuditLog)
    yield audit
    engine.dispose()


def test_default_mode_uses_fake(client: TestClient) -> None:
    assert isinstance(container.get_audit(), FakeAuditLog)
    assert client.get("/api/audit").json() == []


def test_real_adapter_is_selected(real_audit: SqlAuditLog) -> None:
    assert isinstance(container.get_audit(), SqlAuditLog)


def test_health_reports_real_audit(real_audit: SqlAuditLog) -> None:
    assert TestClient(app).get("/api/health").json()["modules"]["audit"] == "real"


def test_api_returns_entries_from_sqlite(real_audit: SqlAuditLog) -> None:
    case_id = uuid4()
    real_audit.record(
        actor="jan.kowalski",
        action="case.created",
        entity_type="case",
        entity_id=str(case_id),
        case_id=case_id,
        payload={"case_number": "UDIP.WAIU.1.2026"},
    )

    response = TestClient(app).get("/api/audit")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["action"] == "case.created"
    assert body[0]["case_id"] == str(case_id)
    assert body[0]["payload"] == {"case_number": "UDIP.WAIU.1.2026"}
    assert body[0]["at"].endswith("Z") or "+00:00" in body[0]["at"]


def test_api_filters_by_case(real_audit: SqlAuditLog) -> None:
    first, second = uuid4(), uuid4()
    for case_id, action in ((first, "case.created"), (second, "case.created")):
        real_audit.record(
            actor="urzędnik",
            action=action,
            entity_type="case",
            entity_id=str(case_id),
            case_id=case_id,
        )

    body = TestClient(app).get("/api/audit", params={"case_id": str(first)}).json()

    assert len(body) == 1
    assert body[0]["case_id"] == str(first)


def test_api_respects_limit(real_audit: SqlAuditLog) -> None:
    for index in range(5):
        real_audit.record(
            actor="urzędnik",
            action=f"case.step_{index}",
            entity_type="case",
            entity_id=str(uuid4()),
        )

    body = TestClient(app).get("/api/audit", params={"limit": 2}).json()

    assert [entry["action"] for entry in body] == ["case.step_4", "case.step_3"]


def test_api_rejects_invalid_limit(real_audit: SqlAuditLog) -> None:
    assert TestClient(app).get("/api/audit", params={"limit": 0}).status_code == 422
    assert TestClient(app).get("/api/audit", params={"limit": 501}).status_code == 422
