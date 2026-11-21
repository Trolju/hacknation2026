"""Testy adaptera `SqlAuditLog` — zapis, odczyt, filtr, limit, kolejność."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, delete, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.adapters.real.audit import SqlAuditLog
from app.modules.audit.models import AuditEntryModel


def _record(audit: SqlAuditLog, action: str, *, case_id: UUID | None = None) -> None:
    audit.record(
        actor="jan.kowalski",
        action=action,
        entity_type="case",
        entity_id=str(case_id or uuid4()),
        case_id=case_id,
        payload={"action": action},
    )


def test_record_then_list_returns_entry(audit: SqlAuditLog) -> None:
    case_id = uuid4()
    audit.record(
        actor="jan.kowalski",
        action="case.created",
        entity_type="case",
        entity_id=str(case_id),
        case_id=case_id,
        payload={"case_number": "UDIP.WAIU.1.2026"},
    )

    entries = audit.list()

    assert len(entries) == 1
    entry = entries[0]
    assert isinstance(entry.id, UUID)
    assert entry.actor == "jan.kowalski"
    assert entry.action == "case.created"
    assert entry.entity_type == "case"
    assert entry.entity_id == str(case_id)
    assert entry.case_id == case_id
    assert entry.payload == {"case_number": "UDIP.WAIU.1.2026"}
    assert entry.at.tzinfo is not None


def test_list_is_ordered_newest_first(audit: SqlAuditLog) -> None:
    for index in range(5):
        _record(audit, f"case.step_{index}")

    actions = [entry.action for entry in audit.list()]

    assert actions == [f"case.step_{index}" for index in reversed(range(5))]


def test_list_filters_by_case(audit: SqlAuditLog) -> None:
    first, second = uuid4(), uuid4()
    _record(audit, "case.created", case_id=first)
    _record(audit, "case.updated", case_id=second)
    _record(audit, "case.transitioned", case_id=first)

    entries = audit.list(case_id=first)

    assert [entry.action for entry in entries] == ["case.transitioned", "case.created"]
    assert {entry.case_id for entry in entries} == {first}


def test_list_respects_limit(audit: SqlAuditLog) -> None:
    for index in range(10):
        _record(audit, f"case.step_{index}")

    assert len(audit.list(limit=3)) == 3
    assert [entry.action for entry in audit.list(limit=2)] == [
        "case.step_9",
        "case.step_8",
    ]


def test_list_limit_is_clamped(audit: SqlAuditLog) -> None:
    _record(audit, "case.created")

    assert len(audit.list(limit=0)) == 1
    assert len(audit.list(limit=10_000)) == 1


def test_payload_accepts_uuid_and_dates(audit: SqlAuditLog) -> None:
    case_id = uuid4()
    audit.record(
        actor="urzędnik",
        action="case.updated",
        entity_type="case",
        entity_id=str(case_id),
        case_id=case_id,
        payload={
            "deadline": date(2026, 3, 30),
            "at": datetime(2026, 3, 16, 12, 0, tzinfo=UTC),
            "document_id": uuid4(),
            "nested": {"ids": [uuid4()]},
        },
    )

    payload = audit.list()[0].payload

    assert payload["deadline"] == "2026-03-30"
    assert payload["at"] == "2026-03-16T12:00:00+00:00"
    assert isinstance(payload["document_id"], str)
    assert isinstance(payload["nested"]["ids"][0], str)


def test_entries_survive_new_adapter_instance(engine: Engine) -> None:
    _record(SqlAuditLog(engine=engine), "case.created")

    assert len(SqlAuditLog(engine=engine).list()) == 1


def test_update_is_rejected(engine: Engine) -> None:
    _record(SqlAuditLog(engine=engine), "case.created")
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with pytest.raises(IntegrityError), factory() as session:
        session.execute(update(AuditEntryModel).values(actor="ktoś inny"))
        session.commit()


def test_delete_is_rejected(engine: Engine) -> None:
    _record(SqlAuditLog(engine=engine), "case.created")
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with pytest.raises(IntegrityError), factory() as session:
        session.execute(delete(AuditEntryModel))
        session.commit()


def test_table_has_expected_columns(engine: Engine) -> None:
    SqlAuditLog(engine=engine)  # tworzy schemat leniwie

    with engine.connect() as connection:
        columns = {
            row[1] for row in connection.execute(text("PRAGMA table_info(audit_entries)"))
        }

    assert columns == {
        "seq",
        "id",
        "at",
        "actor",
        "action",
        "entity_type",
        "entity_id",
        "case_id",
        "payload",
    }


def test_session_factory_is_used_when_given(engine: Engine) -> None:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    audit = SqlAuditLog(engine=engine, session_factory=factory)

    _record(audit, "case.created")

    with factory() as session:
        assert session.query(AuditEntryModel).count() == 1


def test_naive_timestamp_is_read_as_utc(engine: Engine) -> None:
    """SQLite gubi strefę czasową — adapter musi ją odtworzyć jako UTC."""
    audit = SqlAuditLog(engine=engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO audit_entries (id, at, actor, action, entity_type,"
                " entity_id, case_id, payload)"
                " VALUES (:id, :at, 'urzędnik', 'case.created', 'case', 'x', NULL, '{}')"
            ).bindparams(id=str(uuid4()), at=datetime(2026, 3, 16, 8, 30))
        )

    entry = audit.list()[0]

    assert entry.at == datetime(2026, 3, 16, 8, 30, tzinfo=UTC)
