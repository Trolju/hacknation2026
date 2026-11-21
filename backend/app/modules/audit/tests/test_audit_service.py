"""Testy warstwy serwisowej dziennika — `record`, `changed_fields`, zależność."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.adapters.fakes.audit import FakeAuditLog
from app.contracts import CasePatch
from app.core import container
from app.modules.audit.service import (
    AuditAction,
    AuditEntity,
    AuditRecorder,
    audit_recorder,
    changed_fields,
    record,
)


def test_record_writes_through_port() -> None:
    audit = FakeAuditLog()
    case_id = uuid4()

    record(
        audit,
        action=AuditAction.CASE_CREATED,
        entity_type=AuditEntity.CASE,
        entity_id=case_id,
        case_id=case_id,
        payload={"case_number": "UDIP.WAIU.1.2026"},
        actor="jan.kowalski",
    )

    entry = audit.list()[0]
    assert entry.action == "case.created"
    assert entry.entity_type == "case"
    assert entry.entity_id == str(case_id)
    assert entry.case_id == case_id
    assert entry.actor == "jan.kowalski"
    assert entry.payload == {"case_number": "UDIP.WAIU.1.2026"}


def test_record_uses_default_actor() -> None:
    audit = FakeAuditLog()

    record(audit, action=AuditAction.DRAFT_EXPORTED, entity_type=AuditEntity.DRAFT, entity_id="x")

    assert audit.list()[0].actor == "urzędnik"


def test_record_does_not_raise_when_port_fails() -> None:
    class BrokenAuditLog:
        def record(self, **_: Any) -> None:
            raise RuntimeError("baza zablokowana")

        def list(self, **_: Any) -> list[Any]:
            return []

    # Dziennik nie może przewrócić operacji biznesowej.
    record(BrokenAuditLog(), action="case.created", entity_type="case", entity_id="x")


def test_changed_fields_returns_only_submitted_values() -> None:
    assert changed_fields(CasePatch(subject="Nowy temat")) == {"subject": "Nowy temat"}
    assert changed_fields(CasePatch()) == {}


def test_recorder_wraps_port() -> None:
    audit = FakeAuditLog()
    recorder = AuditRecorder(audit)

    recorder.record(
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type=AuditEntity.DOCUMENT,
        entity_id=uuid4(),
    )

    assert audit.list()[0].action == "document.uploaded"


def test_dependency_records_through_container() -> None:
    """Wzorzec z dokumentacji: `Depends(audit_recorder)` w routerze modułu."""
    audit = FakeAuditLog()
    probe_app = FastAPI()
    probe_app.dependency_overrides[container.get_audit] = lambda: audit

    @probe_app.post("/probe")
    def probe(recorder: AuditRecorder = Depends(audit_recorder)) -> dict[str, str]:
        recorder.record(
            action=AuditAction.CASE_TRANSITIONED,
            entity_type=AuditEntity.CASE,
            entity_id=UUID(int=1),
            case_id=UUID(int=1),
            payload={"to": "kwerenda"},
        )
        return {"status": "ok"}

    assert TestClient(probe_app).post("/probe").status_code == 200

    entry = audit.list()[0]
    assert entry.action == "case.transitioned"
    assert entry.case_id == UUID(int=1)
    assert entry.payload == {"to": "kwerenda"}
