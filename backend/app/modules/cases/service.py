"""Logika domenowa wniosków (WS1).

Router tylko deleguje — maszyna stanów a–e, walidacja pól i normalizacja
parametrów listy mieszkają tutaj. Reguły przejść są wspólne dla atrapy
(`app.adapters.fakes.cases`) i repozytorium SQL (`app.adapters.real.cases`),
żeby oba adaptery zachowywały się identycznie.
"""

from __future__ import annotations

import builtins
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from app.contracts import (
    STATUS_ORDER,
    Case,
    CaseCreate,
    CaseDetail,
    CasePatch,
    CaseStatus,
    HistoryEntry,
    TransitionRequest,
)
from app.core.errors import InvalidTransition, ValidationFailed

if TYPE_CHECKING:
    from app.ports.cases import CaseRepositoryPort

MAX_SUBJECT_LENGTH = 200
MIN_INITIALS_LENGTH = 2
MAX_INITIALS_LENGTH = 4

SORT_OPTIONS: tuple[str, ...] = (
    "deadline_asc",
    "deadline_desc",
    "inflow_asc",
    "inflow_desc",
)
DEFAULT_SORT = "inflow_asc"


# ────────────────────────────── maszyna stanów ──────────────────────────────
def _index(status: CaseStatus) -> int:
    return STATUS_ORDER.index(status)


def requires_note(current: CaseStatus, to: CaseStatus) -> bool:
    """Czy przejście wymaga notatki?

    Notatka jest obowiązkowa przy cofnięciu o krok oraz przy wyjściu ze stanu
    końcowego `odpowiedz_wyslana`.
    """
    if current is to:
        return False
    if current is CaseStatus.ODPOWIEDZ_WYSLANA:
        return True
    return _index(to) == _index(current) - 1


def transition_allowed(current: CaseStatus, to: CaseStatus, note: str | None = None) -> bool:
    """Reguły z `contracts/domain.md` §2.

    - naprzód tylko o jeden krok,
    - `kwerenda` jest opcjonalna (`zapytania_wyslane → przygotowana_odpowiedz`),
    - cofnięcie o krok wymaga notatki,
    - wyjście ze stanu końcowego wymaga notatki.
    """
    if current is to:
        return False
    has_note = bool(note and note.strip())
    step = _index(to) - _index(current)
    if step == 1:
        return True
    if current is CaseStatus.ZAPYTANIA_WYSLANE and to is CaseStatus.PRZYGOTOWANA_ODPOWIEDZ:
        return True
    if step == -1:
        return has_note
    if current is CaseStatus.ODPOWIEDZ_WYSLANA:
        return has_note
    return False


def forward_status(current: CaseStatus) -> CaseStatus | None:
    """Następny stan w kolejności a–e (bez pomijania kwerendy)."""
    index = _index(current)
    if index + 1 >= len(STATUS_ORDER):
        return None
    return STATUS_ORDER[index + 1]


def backward_status(current: CaseStatus) -> CaseStatus | None:
    """Poprzedni stan w kolejności a–e — cofnięcie wymaga notatki."""
    index = _index(current)
    if index == 0:
        return None
    return STATUS_ORDER[index - 1]


def skippable_status(current: CaseStatus) -> CaseStatus | None:
    """Stan, który można osiągnąć z pominięciem kwerendy."""
    if current is CaseStatus.ZAPYTANIA_WYSLANE:
        return CaseStatus.PRZYGOTOWANA_ODPOWIEDZ
    return None


# ──────────────────────────────── walidacja ─────────────────────────────────
def validate_subject(subject: str) -> str:
    value = subject.strip()
    if not value:
        raise ValidationFailed(
            "Temat wniosku nie może być pusty.", details={"field": "subject"}
        )
    if len(value) > MAX_SUBJECT_LENGTH:
        raise ValidationFailed(
            f"Temat wniosku może mieć najwyżej {MAX_SUBJECT_LENGTH} znaków.",
            details={"field": "subject", "max_length": MAX_SUBJECT_LENGTH},
        )
    return value


def validate_initials(initials: str) -> str:
    value = initials.strip()
    if not value:
        return ""
    if not MIN_INITIALS_LENGTH <= len(value) <= MAX_INITIALS_LENGTH:
        raise ValidationFailed(
            "Inicjały osoby obsługującej muszą mieć od "
            f"{MIN_INITIALS_LENGTH} do {MAX_INITIALS_LENGTH} znaków.",
            details={"field": "handler_initials"},
        )
    return value


def normalize_sort(sort: str | None) -> str:
    return sort if sort in SORT_OPTIONS else DEFAULT_SORT


def validate_dates(
    *,
    inflow_date: date,
    deadline: date | None,
    response_date: date | None,
) -> None:
    """Spójność dat w sprawie.

    Dane z rejestru UMB zawierają rekordy, w których termin albo data
    odpowiedzi wypadają przed datą wpływu — zwykle to literówka w roku.
    Taki wniosek trafia do kalendarza z ujemnym „pozostało dni” i wygląda
    jak sprawa po terminie, więc odrzucamy go przy zapisie.
    """
    if deadline is not None and deadline < inflow_date:
        raise ValidationFailed(
            "Termin odpowiedzi nie może być wcześniejszy niż data wpływu.",
            details={
                "field": "deadline",
                "inflow_date": inflow_date.isoformat(),
                "deadline": deadline.isoformat(),
            },
        )
    if response_date is not None and response_date < inflow_date:
        raise ValidationFailed(
            "Data odpowiedzi nie może być wcześniejsza niż data wpływu.",
            details={
                "field": "response_date",
                "inflow_date": inflow_date.isoformat(),
                "response_date": response_date.isoformat(),
            },
        )


# ───────────────────────────────── serwis ───────────────────────────────────
class CaseService:
    """Operacje na wnioskach — waliduje wejście i deleguje do repozytorium."""

    def __init__(self, repo: CaseRepositoryPort) -> None:
        self._repo = repo

    def list(
        self,
        *,
        year: int | None = None,
        status: CaseStatus | None = None,
        q: str | None = None,
        sort: str = DEFAULT_SORT,
    ) -> list[Case]:
        needle = q.strip() if q else None
        return self._repo.list(
            year=year,
            status=status,
            q=needle or None,
            sort=normalize_sort(sort),
        )

    def years(self) -> builtins.list[int]:
        return self._repo.years()

    def get(self, case_id: UUID) -> CaseDetail:
        return self._repo.get(case_id)

    def create(self, data: CaseCreate) -> Case:
        validate_dates(
            inflow_date=data.inflow_date,
            deadline=data.deadline,
            response_date=None,
        )
        prepared = data.model_copy(
            update={
                "subject": validate_subject(data.subject),
                "handler_initials": validate_initials(data.handler_initials),
            }
        )
        return self._repo.create(prepared)

    def update(self, case_id: UUID, patch: CasePatch) -> Case:
        changes: dict[str, object] = {}
        if patch.subject is not None:
            changes["subject"] = validate_subject(patch.subject)
        if patch.handler_initials is not None:
            changes["handler_initials"] = validate_initials(patch.handler_initials)
        if patch.deadline is not None or patch.response_date is not None:
            current = self._repo.get(case_id)
            validate_dates(
                inflow_date=current.inflow_date,
                deadline=patch.deadline if patch.deadline is not None else current.deadline,
                response_date=patch.response_date
                if patch.response_date is not None
                else current.response_date,
            )
        prepared = patch.model_copy(update=changes) if changes else patch
        return self._repo.update(case_id, prepared)

    def transition(self, case_id: UUID, body: TransitionRequest) -> Case:
        current = self._repo.get(case_id).status
        note = (body.note or "").strip() or None
        if not transition_allowed(current, body.to, note):
            raise InvalidTransition(
                _transition_message(current, body.to, note),
                details={
                    "from": current.value,
                    "to": body.to.value,
                    "reason": "note_required"
                    if requires_note(current, body.to)
                    else "not_allowed",
                },
            )
        if body.kwerenda_days is not None and body.to is not CaseStatus.KWERENDA:
            raise ValidationFailed(
                "Przedłużenie terminu podaje się tylko przy przejściu do kwerendy.",
                details={"field": "kwerenda_days", "to": body.to.value},
            )
        return self._repo.transition(
            case_id,
            body.to,
            actor=body.actor,
            note=note,
            kwerenda_days=body.kwerenda_days,
        )

    def history(self, case_id: UUID) -> builtins.list[HistoryEntry]:
        return self._repo.history(case_id)


def _transition_message(current: CaseStatus, to: CaseStatus, note: str | None) -> str:
    if requires_note(current, to) and not note:
        return "Cofnięcie stanu wymaga notatki."
    return f"Niedozwolone przejście: {current.value} → {to.value}."
