"""Atrapa repozytorium wniosków — dane z fixtures, stan w pamięci."""

from __future__ import annotations

import builtins
from collections import defaultdict
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from app.adapters.fakes import fixtures
from app.contracts import (
    STATUS_ORDER,
    Case,
    CaseCreate,
    CaseDetail,
    CasePatch,
    CaseStatus,
    HistoryEntry,
)
from app.core.clock import now, today
from app.core.derive import compute
from app.core.errors import InvalidTransition, NotFound
from app.core.settings import settings


def _stamp(inflow_date: str) -> datetime:
    return datetime.fromisoformat(inflow_date + "T08:00:00+00:00")


def _to_case(row: dict) -> Case:
    status = CaseStatus(row["status"])
    days, urgency = compute(status, date.fromisoformat(row["deadline"]))
    return Case(
        id=UUID(row["id"]),
        case_number=row["case_number"],
        ordinal=row["ordinal"],
        subject=row["subject"],
        applicant=row.get("applicant", ""),
        inflow_date=row["inflow_date"],
        deadline=row["deadline"],
        response_date=row.get("response_date"),
        handler_initials=row.get("handler_initials", ""),
        status=status,
        year=int(row["inflow_date"][:4]),
        days_remaining=days,
        urgency=urgency,
        applicant_type=row.get("applicant_type", "inne"),
        source_document_id=row.get("source_document_id"),
        kwerenda_days=row.get("kwerenda_days"),
        created_at=row.get("created_at") or _stamp(row["inflow_date"]),
        updated_at=row.get("updated_at") or _stamp(row["inflow_date"]),
    )


class FakeCaseRepository:
    def __init__(self) -> None:
        self._rows: dict[str, dict] = {r["id"]: dict(r) for r in fixtures.cases()}
        self._history: dict[str, list[HistoryEntry]] = defaultdict(list)
        # Fixture'y opisują sprawy już zarejestrowane w urzędzie — dokładamy wpis
        # o utworzeniu, żeby panel historii nie był pusty przed pierwszą zmianą.
        for row in self._rows.values():
            self._history[row["id"]].append(
                HistoryEntry(
                    id=uuid4(),
                    case_id=UUID(row["id"]),
                    at=_stamp(row["inflow_date"]),
                    actor="urzędnik",
                    action="created",
                    from_value=None,
                    to_value=None,
                    note="wniosek zarejestrowany w urzędzie",
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
    ) -> builtins.list[Case]:
        rows = [_to_case(r) for r in self._rows.values()]
        if year is not None:
            rows = [c for c in rows if c.year == year]
        if status is not None:
            rows = [c for c in rows if c.status == status]
        if q:
            needle = q.lower()
            rows = [
                c
                for c in rows
                if needle in c.subject.lower() or needle in c.case_number.lower()
            ]
        keys = {
            "deadline_asc": lambda c: (c.deadline, c.ordinal),
            "deadline_desc": lambda c: (-c.deadline.toordinal(), c.ordinal),
            "inflow_asc": lambda c: (c.inflow_date, c.ordinal),
            "inflow_desc": lambda c: (-c.inflow_date.toordinal(), c.ordinal),
        }
        return sorted(rows, key=keys.get(sort, keys["inflow_asc"]))

    def years(self) -> builtins.list[int]:
        return sorted({int(r["inflow_date"][:4]) for r in self._rows.values()}, reverse=True)

    def get(self, case_id: UUID) -> CaseDetail:
        row = self._rows.get(str(case_id))
        if row is None:
            raise NotFound("Nie znaleziono wniosku.")
        base = _to_case(row)
        return CaseDetail(
            **base.model_dump(),
            notes=row.get("notes"),
            department_ids=row.get("department_ids", []),
            document_ids=row.get("document_ids", []),
        )

    # ── zapis ──
    def create(self, data: CaseCreate) -> Case:
        cid = str(uuid4())
        year = data.inflow_date.year
        ordinal = 1 + max(
            (r["ordinal"] for r in self._rows.values() if int(r["inflow_date"][:4]) == year),
            default=0,
        )
        deadline = data.deadline or data.inflow_date.fromordinal(
            data.inflow_date.toordinal() + settings.default_response_days
        )
        stamp = now()
        row = {
            "id": cid,
            "case_number": data.case_number,
            "ordinal": ordinal,
            "subject": data.subject,
            "applicant": data.applicant,
            "inflow_date": data.inflow_date.isoformat(),
            "deadline": deadline.isoformat(),
            "response_date": None,
            "handler_initials": data.handler_initials,
            "status": CaseStatus.NOWY.value,
            "applicant_type": data.applicant_type.value,
            "source_document_id": str(data.source_document_id) if data.source_document_id else None,
            "notes": "",
            "created_at": stamp,
            "updated_at": stamp,
        }
        self._rows[cid] = row
        self._log(cid, "created", None, CaseStatus.NOWY.value, "utworzenie wniosku")
        return _to_case(row)

    def update(self, case_id: UUID, patch: CasePatch) -> Case:
        row = self._rows.get(str(case_id))
        if row is None:
            raise NotFound("Nie znaleziono wniosku.")
        data = patch.model_dump(exclude_unset=True)
        for key, value in data.items():
            if value is None:
                continue
            row[key] = value.isoformat() if hasattr(value, "isoformat") else value
        row["updated_at"] = now()
        self._log(str(case_id), "field_update", None, None, "aktualizacja pól")
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
        row = self._rows.get(str(case_id))
        if row is None:
            raise NotFound("Nie znaleziono wniosku.")
        current = CaseStatus(row["status"])
        if not _allowed(current, to, note):
            raise InvalidTransition(
                f"Niedozwolone przejście: {current.value} → {to.value}.",
                details={"from": current.value, "to": to.value},
            )
        row["status"] = to.value
        if to is CaseStatus.KWERENDA and kwerenda_days:
            shifted = date.fromisoformat(row["deadline"]) + timedelta(days=kwerenda_days)
            row["deadline"] = shifted.isoformat()
            row["kwerenda_days"] = (row.get("kwerenda_days") or 0) + kwerenda_days
        if to is CaseStatus.ODPOWIEDZ_WYSLANA and not row.get("response_date"):
            row["response_date"] = today().isoformat()
        row["updated_at"] = now()
        self._log(str(case_id), "status_change", current.value, to.value, note or "", actor)
        return _to_case(row)

    def history(self, case_id: UUID) -> builtins.list[HistoryEntry]:
        return list(self._history.get(str(case_id), []))

    # ── wewnętrzne ──
    def _log(
        self,
        case_id: str,
        action: str,
        from_value: str | None,
        to_value: str | None,
        note: str,
        actor: str = "urzędnik",
    ) -> None:
        self._history[case_id].append(
            HistoryEntry(
                id=uuid4(),
                case_id=UUID(case_id),
                at=now(),
                actor=actor,
                action=action,
                from_value=from_value,
                to_value=to_value,
                note=note or None,
            )
        )


def _allowed(current: CaseStatus, to: CaseStatus, note: str | None) -> bool:
    if current is to:
        return False
    i, j = STATUS_ORDER.index(current), STATUS_ORDER.index(to)
    if j == i + 1:
        return True
    # pominięcie kwerendy: zapytania_wyslane → przygotowana_odpowiedz
    if current is CaseStatus.ZAPYTANIA_WYSLANE and to is CaseStatus.PRZYGOTOWANA_ODPOWIEDZ:
        return True
    # cofnięcie o krok wymaga notatki
    if j == i - 1:
        return bool(note)
    # wyjście ze stanu końcowego wymaga notatki
    if current is CaseStatus.ODPOWIEDZ_WYSLANA:
        return bool(note)
    return False
