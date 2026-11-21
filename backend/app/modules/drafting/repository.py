"""Zapis projektu odpowiedzi w SQLite wraz z historią wersji.

Repozytorium jest wewnętrzne dla modułu — port `DraftingPort` nie zna pojęcia
wersji, bo kontrakt API jest zamrożony. Historia jest jednak potrzebna
urzędnikowi: każda korekta zostawia migawkę treści wraz z autorem i powodem.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.contracts import Citation, Draft
from app.core.clock import now
from app.core.db import Base
from app.core.db import engine as default_engine
from app.modules.drafting.models import DraftHistoryRow, DraftRow


@dataclass(frozen=True)
class DraftVersion:
    """Migawka jednej wersji projektu — kto, kiedy i jaka treść."""

    id: UUID
    draft_id: UUID
    at: datetime
    actor: str
    action: str
    version: int
    title: str
    body: str
    note: str | None


def _as_utc(value: datetime) -> datetime:
    """SQLite gubi strefę czasową — znaczniki zawsze zwracamy jako UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _dump_citations(citations: list[Citation]) -> str:
    return json.dumps([item.model_dump() for item in citations], ensure_ascii=False)


def _load_citations(raw: str | None) -> list[Citation]:
    if not raw:
        return []
    return [Citation(**item) for item in json.loads(raw)]


def _dump_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def _load_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [str(item) for item in json.loads(raw)]


def _to_draft(row: DraftRow) -> Draft:
    return Draft(
        id=UUID(row.id),
        case_id=UUID(row.case_id),
        title=row.title,
        body=row.body,
        citations=_load_citations(row.citations),
        unsupported=_load_list(row.unsupported),
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at) if row.updated_at else None,
    )


def _to_version(row: DraftHistoryRow) -> DraftVersion:
    return DraftVersion(
        id=UUID(row.id),
        draft_id=UUID(row.draft_id),
        at=_as_utc(row.at),
        actor=row.actor,
        action=row.action,
        version=row.version,
        title=row.title,
        body=row.body,
        note=row.note,
    )


def _draft_tables() -> list[Any]:
    """Tabele tego modułu — tworzymy tylko własne, nie ruszamy cudzych."""
    return [Base.metadata.tables[name] for name in ("drafts", "draft_history")]


class DraftRepository:
    """Projekty odpowiedzi i ich historia w SQLite."""

    def __init__(self, engine: Engine | None = None) -> None:
        self._engine = engine or default_engine
        self._session_factory: sessionmaker[Session] = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )
        Base.metadata.create_all(bind=self._engine, tables=_draft_tables())

    @contextmanager
    def _session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ── odczyt ──
    def get(self, draft_id: UUID) -> Draft | None:
        with self._session() as session:
            row = session.get(DraftRow, str(draft_id))
            return _to_draft(row) if row is not None else None

    def get_by_case(self, case_id: UUID) -> Draft | None:
        with self._session() as session:
            row = session.scalar(
                select(DraftRow).where(DraftRow.case_id == str(case_id))
            )
            return _to_draft(row) if row is not None else None

    def history(self, draft_id: UUID) -> list[DraftVersion]:
        with self._session() as session:
            rows = session.scalars(
                select(DraftHistoryRow)
                .where(DraftHistoryRow.draft_id == str(draft_id))
                .order_by(DraftHistoryRow.version.asc(), DraftHistoryRow.at.asc())
            ).all()
            return [_to_version(row) for row in rows]

    # ── zapis ──
    def save(
        self,
        draft: Draft,
        *,
        actor: str,
        action: str,
        note: str | None = None,
    ) -> Draft:
        """Zapisuje projekt i dopisuje migawkę wersji do historii."""
        with self._session() as session:
            row = session.get(DraftRow, str(draft.id))
            if row is None:
                row = DraftRow(
                    id=str(draft.id),
                    case_id=str(draft.case_id),
                    title=draft.title,
                    body=draft.body,
                    citations=_dump_citations(draft.citations),
                    unsupported=_dump_list(draft.unsupported),
                    version=1,
                    created_at=draft.created_at,
                    updated_at=draft.updated_at,
                )
                session.add(row)
            else:
                row.title = draft.title
                row.body = draft.body
                row.citations = _dump_citations(draft.citations)
                row.unsupported = _dump_list(draft.unsupported)
                row.version += 1
                row.updated_at = draft.updated_at or now()
            session.add(
                DraftHistoryRow(
                    id=str(uuid4()),
                    draft_id=row.id,
                    at=now(),
                    actor=actor,
                    action=action,
                    version=row.version,
                    title=row.title,
                    body=row.body,
                    note=note,
                )
            )
            session.flush()
            return _to_draft(row)
