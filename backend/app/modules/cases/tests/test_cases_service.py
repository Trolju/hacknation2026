"""Serwis wniosków: maszyna stanów, walidacja i normalizacja parametrów."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.contracts import CaseCreate, CasePatch, CaseStatus, TransitionRequest
from app.core.errors import InvalidTransition, NotFound, ValidationFailed
from app.modules.cases.service import (
    CaseService,
    backward_status,
    forward_status,
    normalize_sort,
    requires_note,
    skippable_status,
    transition_allowed,
    validate_initials,
    validate_subject,
)

NOWY = CaseStatus.NOWY
ZAPYTANIA = CaseStatus.ZAPYTANIA_WYSLANE
KWERENDA = CaseStatus.KWERENDA
PRZYGOTOWANA = CaseStatus.PRZYGOTOWANA_ODPOWIEDZ
WYSLANA = CaseStatus.ODPOWIEDZ_WYSLANA


# ─────────────────────────────── maszyna stanów ─────────────────────────────
@pytest.mark.parametrize(
    ("current", "to"),
    [
        (NOWY, ZAPYTANIA),
        (ZAPYTANIA, KWERENDA),
        (KWERENDA, PRZYGOTOWANA),
        (PRZYGOTOWANA, WYSLANA),
        (ZAPYTANIA, PRZYGOTOWANA),
    ],
)
def test_forward_transitions_allowed_without_note(current: CaseStatus, to: CaseStatus) -> None:
    assert transition_allowed(current, to) is True
    assert requires_note(current, to) is False


@pytest.mark.parametrize(
    ("current", "to"),
    [
        (NOWY, KWERENDA),
        (NOWY, PRZYGOTOWANA),
        (NOWY, WYSLANA),
        (ZAPYTANIA, WYSLANA),
        (KWERENDA, NOWY),
        (PRZYGOTOWANA, ZAPYTANIA),
        (NOWY, NOWY),
        (WYSLANA, NOWY),
    ],
)
def test_forbidden_transitions(current: CaseStatus, to: CaseStatus) -> None:
    assert transition_allowed(current, to) is False


@pytest.mark.parametrize(
    ("current", "to"),
    [
        (ZAPYTANIA, NOWY),
        (KWERENDA, ZAPYTANIA),
        (PRZYGOTOWANA, KWERENDA),
        (WYSLANA, PRZYGOTOWANA),
    ],
)
def test_backward_transitions_require_note(current: CaseStatus, to: CaseStatus) -> None:
    assert requires_note(current, to) is True
    assert transition_allowed(current, to) is False
    assert transition_allowed(current, to, "notatka") is True


def test_blank_note_does_not_unlock_backward_transition() -> None:
    assert transition_allowed(ZAPYTANIA, NOWY, "   ") is False


def test_status_helpers_follow_order() -> None:
    assert forward_status(NOWY) is ZAPYTANIA
    assert forward_status(WYSLANA) is None
    assert backward_status(NOWY) is None
    assert backward_status(WYSLANA) is PRZYGOTOWANA
    assert skippable_status(ZAPYTANIA) is PRZYGOTOWANA
    assert skippable_status(NOWY) is None


# ──────────────────────────────── walidacja ─────────────────────────────────
def test_validate_subject_strips_and_accepts() -> None:
    assert validate_subject("  Temat  ") == "Temat"


def test_validate_subject_rejects_blank() -> None:
    with pytest.raises(ValidationFailed) as excinfo:
        validate_subject("   ")
    assert excinfo.value.details["field"] == "subject"


def test_validate_subject_rejects_too_long() -> None:
    with pytest.raises(ValidationFailed):
        validate_subject("x" * 201)


def test_validate_initials_accepts_empty_and_range() -> None:
    assert validate_initials("") == ""
    assert validate_initials(" JK ") == "JK"


@pytest.mark.parametrize("value", ["J", "ABCDE"])
def test_validate_initials_rejects_wrong_length(value: str) -> None:
    with pytest.raises(ValidationFailed):
        validate_initials(value)


def test_normalize_sort_falls_back_to_default() -> None:
    assert normalize_sort("inflow_desc") == "inflow_desc"
    assert normalize_sort("cokolwiek") == "deadline_asc"
    assert normalize_sort(None) == "deadline_asc"


# ───────────────────────────────── serwis ───────────────────────────────────
def test_service_create_normalizes_subject(service: CaseService) -> None:
    created = service.create(
        CaseCreate(
            case_number="UDIP.1435.90.2026",
            subject="  Wniosek z serwisu  ",
            inflow_date=date(2026, 3, 16),
            handler_initials="JK",
        )
    )
    assert created.subject == "Wniosek z serwisu"


def test_service_create_rejects_invalid_initials(service: CaseService) -> None:
    with pytest.raises(ValidationFailed):
        service.create(
            CaseCreate(
                case_number="UDIP.1435.91.2026",
                subject="Wniosek",
                inflow_date=date(2026, 3, 16),
                handler_initials="X",
            )
        )


def test_service_update_validates_subject(service: CaseService) -> None:
    case_id = service.list()[0].id
    with pytest.raises(ValidationFailed):
        service.update(case_id, CasePatch(subject="   "))


def test_service_transition_requires_note_for_backward(service: CaseService) -> None:
    case_id = service.list(status=NOWY)[0].id
    service.transition(case_id, TransitionRequest(to=ZAPYTANIA))
    with pytest.raises(InvalidTransition) as excinfo:
        service.transition(case_id, TransitionRequest(to=NOWY))
    assert excinfo.value.code == "invalid_transition"
    assert excinfo.value.status_code == 409
    assert excinfo.value.details["reason"] == "note_required"
    assert "notatki" in excinfo.value.message


def test_service_transition_reports_forbidden_step(service: CaseService) -> None:
    case_id = service.list(status=NOWY)[0].id
    with pytest.raises(InvalidTransition) as excinfo:
        service.transition(case_id, TransitionRequest(to=KWERENDA))
    assert excinfo.value.details["reason"] == "not_allowed"


def test_service_transition_unknown_case_raises_not_found(service: CaseService) -> None:
    with pytest.raises(NotFound):
        service.transition(uuid4(), TransitionRequest(to=ZAPYTANIA))


def test_service_list_strips_query(service: CaseService) -> None:
    assert [row.case_number for row in service.list(q="  wynagrodze  ")] == [
        "UDIP.1435.1.2026"
    ]


def test_service_list_ignores_unknown_sort(service: CaseService) -> None:
    deadlines = [row.deadline for row in service.list(sort="nieznane")]
    assert deadlines == sorted(deadlines)


def test_service_history_returns_entries(service: CaseService) -> None:
    case_id = service.list(status=NOWY)[0].id
    service.transition(case_id, TransitionRequest(to=ZAPYTANIA, actor="Jan Kowalski"))
    history = service.history(case_id)
    assert history and history[-1].actor == "Jan Kowalski"
