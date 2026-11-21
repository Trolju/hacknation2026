"""Dziennik audytu na SQLAlchemy 2.0 + SQLite (WS8).

Implementacja portu `app/ports/audit.py`. Tabela `audit_entries` jest tylko
dopisywana: adapter nie ma metod aktualizacji ani usuwania, a wyzwalacze SQLite
odrzucają `UPDATE` i `DELETE` wykonane z zewnątrz.

Schemat tworzony jest leniwie przy pierwszym użyciu adaptera, więc włączenie
`MODULE_MODE_AUDIT=real` nie wymaga migracji ani ręcznego `create_all()`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import Engine, Table, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.contracts import AuditEntry
from app.modules.audit.models import TABLE_NAME, AuditEntryModel

DEFAULT_LIMIT = 100
MAX_LIMIT = 500

_APPEND_ONLY_DDL: tuple[str, ...] = (
    f"""
    CREATE TRIGGER IF NOT EXISTS {TABLE_NAME}_no_update
    BEFORE UPDATE ON {TABLE_NAME}
    BEGIN
        SELECT RAISE(ABORT, 'dziennik audytu jest tylko dopisywany');
    END
    """,
    f"""
    CREATE TRIGGER IF NOT EXISTS {TABLE_NAME}_no_delete
    BEFORE DELETE ON {TABLE_NAME}
    BEGIN
        SELECT RAISE(ABORT, 'dziennik audytu jest tylko dopisywany');
    END
    """,
)


def _json_safe(value: Any) -> Any:
    """Sprowadza payload do typów JSON.

    Zdarzenia audytu niosą identyfikatory UUID i daty — bez tej konwersji
    zapis wywaliłby się na serializacji.
    """
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


class SqlAuditLog:
    """Port `AuditPort` na tabeli `audit_entries`."""

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        session_factory: sessionmaker[Session] | None = None,
    ) -> None:
        # Import w konstruktorze: `app.core.db` tworzy silnik przy imporcie,
        # a testy podmieniają go na bazę tymczasową.
        from app.core import db as _db

        self._engine: Engine = engine if engine is not None else _db.engine
        self._session_factory: sessionmaker[Session] = (
            session_factory
            if session_factory is not None
            else sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)
        )
        self._ensure_schema()

    # ── schemat ──────────────────────────────────────────────────────────
    def _ensure_schema(self) -> None:
        # `__table__` jest w typach SQLAlchemy 2.1 deklarowane jako `FromClause`,
        # a w runtime to zawsze `Table` — stąd rzutowanie.
        table = cast(Table, AuditEntryModel.__table__)
        table.create(bind=self._engine, checkfirst=True)
        with self._engine.begin() as connection:
            for ddl in _APPEND_ONLY_DDL:
                connection.execute(text(ddl))

    # ── port ─────────────────────────────────────────────────────────────
    def record(
        self,
        *,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        case_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditEntryModel(
            id=str(uuid4()),
            at=datetime.now(UTC),
            actor=actor,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            case_id=str(case_id) if case_id is not None else None,
            payload=_json_safe(payload or {}),
        )
        with self._session_factory() as session:
            session.add(entry)
            session.commit()

    def list(self, *, case_id: UUID | None = None, limit: int = DEFAULT_LIMIT) -> list[AuditEntry]:
        safe_limit = max(1, min(int(limit), MAX_LIMIT))
        statement = (
            select(AuditEntryModel)
            .order_by(AuditEntryModel.seq.desc())
            .limit(safe_limit)
        )
        if case_id is not None:
            statement = statement.where(AuditEntryModel.case_id == str(case_id))
        with self._session_factory() as session:
            rows = session.scalars(statement).all()
        return [self._to_dto(row) for row in rows]

    # ── mapowanie ────────────────────────────────────────────────────────
    @staticmethod
    def _to_dto(row: AuditEntryModel) -> AuditEntry:
        at = row.at
        if at.tzinfo is None:
            # SQLite nie przechowuje strefy — zapisujemy i czytamy zawsze UTC.
            at = at.replace(tzinfo=UTC)
        return AuditEntry(
            id=UUID(row.id),
            at=at,
            actor=row.actor,
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            case_id=UUID(row.case_id) if row.case_id else None,
            payload=row.payload or {},
        )
