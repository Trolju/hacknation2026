"""Repozytorium wniosków na SQLAlchemy 2.0 (SQLite).

Implementacja `app.ports.cases.CaseRepositoryPort`. Pola wyliczane
(`days_remaining`, `urgency`, `year`) nie są zapisywane — liczy je
`app.core.derive` przy każdym odczycie, więc nie rozjeżdżają się z czasem.

Reguły przejść są wspólne z serwisem (`app.modules.cases.service`), żeby atrapa
i repozytorium SQL zachowywały się identycznie.
"""

from __future__ import annotations

import builtins
import json
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Engine, extract, func, select
from sqlalchemy import text as sql_text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.contracts import (
    ApplicantType,
    Case,
    CaseCreate,
    CaseDetail,
    CasePatch,
    CaseStatus,
    HistoryEntry,
)
from app.core.clock import now, today
from app.core.db import Base
from app.core.db import engine as default_engine
from app.core.derive import compute
from app.core.errors import Conflict, InvalidTransition, NotFound
from app.core.settings import settings
from app.modules.cases.models import CaseHistoryRow, CaseRow
from app.modules.cases.service import transition_allowed

DEFAULT_ACTOR = "urzędnik"


# ──────────────────────────────── mapowanie ─────────────────────────────────
def _as_utc(value: datetime) -> datetime:
    """SQLite gubi strefę czasową — znaczniki zawsze zwracamy jako UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_case(row: CaseRow) -> Case:
    status = CaseStatus(row.status)
    days, urgency = compute(status, row.deadline)
    return Case(
        id=UUID(row.id),
        case_number=row.case_number,
        ordinal=row.ordinal,
        subject=row.subject,
        applicant=row.applicant,
        inflow_date=row.inflow_date,
        deadline=row.deadline,
        response_date=row.response_date,
        handler_initials=row.handler_initials,
        status=status,
        year=row.inflow_date.year,
        days_remaining=days,
        urgency=urgency,
        applicant_type=ApplicantType(row.applicant_type),
        source_document_id=UUID(row.source_document_id) if row.source_document_id else None,
        kwerenda_days=row.kwerenda_days,
        created_at=_as_utc(row.created_at),
        updated_at=_as_utc(row.updated_at),
    )


def _to_detail(row: CaseRow) -> CaseDetail:
    return CaseDetail(
        **_to_case(row).model_dump(),
        notes=row.notes,
        department_ids=list(row.department_ids or []),
        document_ids=[UUID(value) for value in (row.document_ids or [])],
    )


def _to_history(row: CaseHistoryRow) -> HistoryEntry:
    return HistoryEntry(
        id=UUID(row.id),
        case_id=UUID(row.case_id),
        at=_as_utc(row.at),
        actor=row.actor,
        action=row.action,
        from_value=row.from_value,
        to_value=row.to_value,
        note=row.note,
    )


def _case_tables() -> list[Any]:
    """Tabele tego modułu — tworzymy tylko własne, nie ruszamy cudzych."""
    return [Base.metadata.tables[name] for name in ("cases", "case_history")]


def _order_by(sort: str) -> tuple[Any, ...]:
    match sort:
        case "deadline_desc":
            return (CaseRow.deadline.desc(), CaseRow.ordinal.asc())
        case "inflow_asc":
            return (CaseRow.inflow_date.asc(), CaseRow.ordinal.asc())
        case "inflow_desc":
            return (CaseRow.inflow_date.desc(), CaseRow.ordinal.asc())
        case _:
            return (CaseRow.deadline.asc(), CaseRow.ordinal.asc())


def _matches(row: CaseRow, needle: str) -> bool:
    return needle in row.subject.lower() or needle in row.case_number.lower()


# ──────────────────────────────── repozytorium ──────────────────────────────
class SqlCaseRepository:
    """Wnioski w SQLite. Tabele `cases` i `case_history`."""

    def __init__(self, engine: Engine | None = None, *, seed: bool = True) -> None:
        self._engine = engine or default_engine
        self._session_factory: sessionmaker[Session] = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )
        self._create_schema()
        if seed:
            self._seed_if_empty()

    # ── infrastruktura ──
    def _create_schema(self) -> None:
        Base.metadata.create_all(bind=self._engine, tables=_case_tables())
        self._ensure_columns()

    def _ensure_columns(self) -> None:
        """Dokłada kolumny dodane po pierwszym uruchomieniu.

        `create_all` tworzy tylko brakujące tabele — istniejącej bazy nie
        zmienia. Bez tego uruchomienie na bazie z poprzedniej wersji kończyłoby
        się błędem „no such column: cases.kwerenda_days”.
        """
        try:
            with self._engine.begin() as conn:
                existing = {
                    row[1] for row in conn.execute(sql_text("PRAGMA table_info(cases)")).all()
                }
                if existing and "kwerenda_days" not in existing:
                    conn.execute(
                        sql_text("ALTER TABLE cases ADD COLUMN kwerenda_days INTEGER")
                    )
                if existing and "applicant" not in existing:
                    conn.execute(
                        sql_text(
                            "ALTER TABLE cases ADD COLUMN applicant VARCHAR(200) "
                            "NOT NULL DEFAULT ''"
                        )
                    )
        except Exception:  # nie-SQLite albo baza tylko do odczytu
            pass

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

    def _seed_if_empty(self) -> None:
        """Pierwsze uruchomienie w trybie `real` startuje z danymi demo."""
        with self._session() as session:
            if not session.scalar(select(func.count()).select_from(CaseRow)):
                for raw in _fixture_rows():
                    session.add(_row_from_fixture(raw))
                session.flush()
            self._backfill_creation_entries(session)

    def _backfill_creation_entries(self, session: Session) -> None:
        """Dopisuje wpis o utworzeniu sprawom, które go jeszcze nie mają.

        Fixture'y opisują sprawy już zarejestrowane w urzędzie, więc panel
        historii nie może być pusty przed pierwszą zmianą. Uzupełniamy też
        bazy z poprzedniej wersji — inaczej po aktualizacji historia zostałaby
        pusta dla wszystkich istniejących spraw.
        """
        logged = set(
            session.scalars(
                select(CaseHistoryRow.case_id).where(CaseHistoryRow.action == "created")
            ).all()
        )
        for row in session.scalars(select(CaseRow)).all():
            if row.id in logged:
                continue
            session.add(
                CaseHistoryRow(
                    id=str(uuid4()),
                    case_id=row.id,
                    at=datetime.combine(row.inflow_date, time(8, 0), tzinfo=UTC),
                    actor=DEFAULT_ACTOR,
                    action="created",
                    from_value=None,
                    to_value=None,
                    note="wniosek zarejestrowany w urzędzie",
                )
            )

    def _require(self, session: Session, case_id: UUID) -> CaseRow:
        row = session.get(CaseRow, str(case_id))
        if row is None:
            raise NotFound("Nie znaleziono wniosku.")
        return row

    def _log(
        self,
        session: Session,
        case_id: str,
        action: str,
        from_value: str | None,
        to_value: str | None,
        note: str | None,
        actor: str = DEFAULT_ACTOR,
    ) -> None:
        session.add(
            CaseHistoryRow(
                id=str(uuid4()),
                case_id=case_id,
                at=now(),
                actor=actor,
                action=action,
                from_value=from_value,
                to_value=to_value,
                note=note or None,
            )
        )

    # ── odczyt ──
    def list(
        self,
        *,
        year: int | None = None,
        status: CaseStatus | None = None,
        q: str | None = None,
        sort: str = "inflow_asc",
    ) -> list[Case]:
        with self._session() as session:
            stmt = select(CaseRow)
            if year is not None:
                stmt = stmt.where(extract("year", CaseRow.inflow_date) == year)
            if status is not None:
                stmt = stmt.where(CaseRow.status == status.value)
            stmt = stmt.order_by(*_order_by(sort))
            rows = list(session.scalars(stmt).all())
        # SQLite `lower()` nie składa polskich znaków, więc tekst filtrujemy
        # w Pythonie — dzięki temu atrapa i repozytorium SQL działają tak samo.
        if q:
            needle = q.lower()
            rows = [row for row in rows if _matches(row, needle)]
        return [_to_case(row) for row in rows]

    def years(self) -> builtins.list[int]:
        with self._session() as session:
            values = session.scalars(select(extract("year", CaseRow.inflow_date))).all()
        return sorted({int(value) for value in values if value is not None}, reverse=True)

    def get(self, case_id: UUID) -> CaseDetail:
        with self._session() as session:
            return _to_detail(self._require(session, case_id))

    def history(self, case_id: UUID) -> builtins.list[HistoryEntry]:
        with self._session() as session:
            rows = session.scalars(
                select(CaseHistoryRow)
                .where(CaseHistoryRow.case_id == str(case_id))
                .order_by(CaseHistoryRow.at.asc(), CaseHistoryRow.id.asc())
            ).all()
            return [_to_history(row) for row in rows]

    # ── zapis ──
    def create(self, data: CaseCreate) -> Case:
        with self._session() as session:
            year = data.inflow_date.year
            last_ordinal = session.scalar(
                select(func.coalesce(func.max(CaseRow.ordinal), 0)).where(
                    extract("year", CaseRow.inflow_date) == year
                )
            )
            deadline = data.deadline or data.inflow_date + timedelta(
                days=settings.default_response_days
            )
            stamp = now()
            row = CaseRow(
                id=str(uuid4()),
                case_number=data.case_number,
                ordinal=int(last_ordinal or 0) + 1,
                subject=data.subject,
                applicant=data.applicant,
                inflow_date=data.inflow_date,
                deadline=deadline,
                response_date=None,
                handler_initials=data.handler_initials,
                status=CaseStatus.NOWY.value,
                applicant_type=data.applicant_type.value,
                source_document_id=str(data.source_document_id)
                if data.source_document_id
                else None,
                notes="",
                department_ids=[],
                document_ids=[],
                created_at=stamp,
                updated_at=stamp,
            )
            session.add(row)
            try:
                session.flush()
            except IntegrityError as exc:
                raise Conflict(
                    "Wniosek o tym numerze już istnieje.",
                    details={"field": "case_number", "case_number": data.case_number},
                ) from exc
            self._log(
                session, row.id, "created", None, CaseStatus.NOWY.value, "utworzenie wniosku"
            )
            session.flush()
            return _to_case(row)

    def update(self, case_id: UUID, patch: CasePatch) -> Case:
        with self._session() as session:
            row = self._require(session, case_id)
            for key, value in patch.model_dump(exclude_unset=True).items():
                if value is None:
                    continue
                if key == "applicant_type":
                    row.applicant_type = ApplicantType(value).value
                elif key == "department_ids":
                    row.department_ids = [str(item) for item in value]
                else:
                    setattr(row, key, value)
            row.updated_at = now()
            self._log(session, row.id, "field_update", None, None, "aktualizacja pól")
            session.flush()
            return _to_case(row)

    def transition(
        self,
        case_id: UUID,
        to: CaseStatus,
        *,
        actor: str,
        note: str | None = None,
        kwerenda_days: int | None = None,
    ) -> Case:
        with self._session() as session:
            row = self._require(session, case_id)
            current = CaseStatus(row.status)
            if not transition_allowed(current, to, note):
                raise InvalidTransition(
                    f"Niedozwolone przejście: {current.value} → {to.value}.",
                    details={"from": current.value, "to": to.value},
                )
            row.status = to.value
            if to is CaseStatus.KWERENDA and kwerenda_days:
                # Termin przesuwa się o przedłużenie; kolejne wejścia w kwerendę
                # sumują się, bo urzędnik może wracać do stanu po cofnięciu.
                row.deadline = row.deadline + timedelta(days=kwerenda_days)
                row.kwerenda_days = (row.kwerenda_days or 0) + kwerenda_days
            if to is CaseStatus.ODPOWIEDZ_WYSLANA and row.response_date is None:
                row.response_date = today()
            row.updated_at = now()
            self._log(
                session, row.id, "status_change", current.value, to.value, note, actor
            )
            session.flush()
            return _to_case(row)


# ──────────────────────────────── dane demo ─────────────────────────────────
def _fixture_rows() -> list[dict[str, Any]]:
    path: Path = settings.fixtures_dir / "cases" / "cases.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _row_from_fixture(raw: dict[str, Any]) -> CaseRow:
    inflow = date.fromisoformat(raw["inflow_date"])
    stamp = datetime.combine(inflow, time(8, 0), tzinfo=UTC)
    return CaseRow(
        id=raw["id"],
        case_number=raw["case_number"],
        ordinal=int(raw["ordinal"]),
        subject=raw["subject"],
        applicant=raw.get("applicant", ""),
        inflow_date=inflow,
        deadline=date.fromisoformat(raw["deadline"]),
        response_date=date.fromisoformat(raw["response_date"])
        if raw.get("response_date")
        else None,
        handler_initials=raw.get("handler_initials", ""),
        status=raw["status"],
        applicant_type=raw.get("applicant_type", ApplicantType.INNE.value),
        source_document_id=raw.get("source_document_id"),
        notes=raw.get("notes") or None,
        department_ids=list(raw.get("department_ids") or []),
        document_ids=list(raw.get("document_ids") or []),
        created_at=stamp,
        updated_at=stamp,
    )
