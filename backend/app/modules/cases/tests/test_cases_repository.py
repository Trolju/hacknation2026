"""CRUD, filtry, sortowanie i historia — na atrapie i na repozytorium SQL."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from app.contracts import CaseCreate, CasePatch, CaseStatus
from app.core.errors import InvalidTransition, NotFound
from app.ports.cases import CaseRepositoryPort

FIXTURE_COUNT = 10


# ────────────────────────────────── odczyt ──────────────────────────────────
def test_list_returns_all_fixture_cases(repo: CaseRepositoryPort) -> None:
    rows = repo.list()
    assert len(rows) == FIXTURE_COUNT
    assert {row.case_number for row in rows} >= {"UDIP.1435.1.2026", "UDIP.1435.10.2026"}


def test_list_sorted_by_deadline_asc(repo: CaseRepositoryPort) -> None:
    deadlines = [row.deadline for row in repo.list(sort="deadline_asc")]
    assert deadlines == sorted(deadlines)


def test_list_sorted_by_deadline_desc(repo: CaseRepositoryPort) -> None:
    deadlines = [row.deadline for row in repo.list(sort="deadline_desc")]
    assert deadlines == sorted(deadlines, reverse=True)


def test_list_sorted_by_inflow(repo: CaseRepositoryPort) -> None:
    asc = [row.inflow_date for row in repo.list(sort="inflow_asc")]
    desc = [row.inflow_date for row in repo.list(sort="inflow_desc")]
    assert asc == sorted(asc)
    assert desc == sorted(desc, reverse=True)


def test_filter_by_year(repo: CaseRepositoryPort) -> None:
    rows = repo.list(year=2026)
    assert rows and all(row.year == 2026 for row in rows)
    assert repo.list(year=1999) == []


def test_filter_by_status(repo: CaseRepositoryPort) -> None:
    rows = repo.list(status=CaseStatus.NOWY)
    assert rows and all(row.status is CaseStatus.NOWY for row in rows)


def test_search_matches_subject_and_case_number(repo: CaseRepositoryPort) -> None:
    by_subject = repo.list(q="wynagrodze")
    assert [row.case_number for row in by_subject] == ["UDIP.1435.1.2026"]
    by_number = repo.list(q="UDIP.1435.7")
    assert [row.case_number for row in by_number] == ["UDIP.1435.7.2026"]
    assert repo.list(q="nie-ma-takiego-wniosku") == []


def test_years_are_unique_and_descending(repo: CaseRepositoryPort) -> None:
    assert repo.years() == [2026]


def test_get_returns_detail(repo: CaseRepositoryPort) -> None:
    case_id = repo.list()[0].id
    detail = repo.get(case_id)
    assert detail.id == case_id
    assert isinstance(detail.department_ids, list)
    assert isinstance(detail.document_ids, list)


def test_get_missing_raises_not_found(repo: CaseRepositoryPort) -> None:
    with pytest.raises(NotFound):
        repo.get(uuid4())


# ────────────────────────────────── zapis ──────────────────────────────────
def test_create_assigns_ordinal_and_default_deadline(repo: CaseRepositoryPort) -> None:
    created = repo.create(
        CaseCreate(
            case_number="UDIP.1435.99.2026",
            subject="Wniosek testowy",
            inflow_date=date(2026, 3, 16),
        )
    )
    assert created.ordinal == FIXTURE_COUNT + 1
    assert created.deadline == date(2026, 3, 30)
    assert created.status is CaseStatus.NOWY
    assert created.year == 2026
    assert created.days_remaining == 14
    assert created.urgency.value == "normal"


def test_create_keeps_explicit_deadline(repo: CaseRepositoryPort) -> None:
    created = repo.create(
        CaseCreate(
            case_number="UDIP.1435.98.2026",
            subject="Wniosek z terminem ręcznym",
            inflow_date=date(2026, 3, 10),
            deadline=date(2026, 3, 16),
        )
    )
    assert created.deadline == date(2026, 3, 16)
    assert created.days_remaining == 0
    assert created.urgency.value == "today"


def test_create_writes_history(repo: CaseRepositoryPort) -> None:
    created = repo.create(
        CaseCreate(
            case_number="UDIP.1435.97.2026",
            subject="Historia utworzenia",
            inflow_date=date(2026, 3, 16),
        )
    )
    history = repo.history(created.id)
    assert [entry.action for entry in history] == ["created"]
    assert history[0].to_value == CaseStatus.NOWY.value


def test_update_changes_fields_and_writes_history(repo: CaseRepositoryPort) -> None:
    case_id = repo.list()[0].id
    updated = repo.update(
        case_id,
        CasePatch(subject="Nowy temat", handler_initials="AB", notes="Notatka urzędnika"),
    )
    assert updated.subject == "Nowy temat"
    assert updated.handler_initials == "AB"
    detail = repo.get(case_id)
    assert detail.notes == "Notatka urzędnika"
    assert "field_update" in [entry.action for entry in repo.history(case_id)]


def test_update_missing_raises_not_found(repo: CaseRepositoryPort) -> None:
    with pytest.raises(NotFound):
        repo.update(uuid4(), CasePatch(subject="Brak sprawy"))


# ─────────────────────────────── maszyna stanów ─────────────────────────────
def _first_with(repo: CaseRepositoryPort, status: CaseStatus) -> UUID:
    return repo.list(status=status)[0].id


def test_transition_forward(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    moved = repo.transition(case_id, CaseStatus.ZAPYTANIA_WYSLANE, actor="urzędnik")
    assert moved.status is CaseStatus.ZAPYTANIA_WYSLANE


def test_transition_skips_kwerenda(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.ZAPYTANIA_WYSLANE)
    moved = repo.transition(case_id, CaseStatus.PRZYGOTOWANA_ODPOWIEDZ, actor="urzędnik")
    assert moved.status is CaseStatus.PRZYGOTOWANA_ODPOWIEDZ


def test_transition_backward_requires_note(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    repo.transition(case_id, CaseStatus.ZAPYTANIA_WYSLANE, actor="urzędnik")
    with pytest.raises(InvalidTransition):
        repo.transition(case_id, CaseStatus.NOWY, actor="urzędnik")


def test_transition_backward_with_note(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    repo.transition(case_id, CaseStatus.ZAPYTANIA_WYSLANE, actor="urzędnik")
    moved = repo.transition(
        case_id, CaseStatus.NOWY, actor="urzędnik", note="Wysłano przez pomyłkę"
    )
    assert moved.status is CaseStatus.NOWY


def test_transition_two_steps_forward_is_forbidden(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    with pytest.raises(InvalidTransition):
        repo.transition(case_id, CaseStatus.KWERENDA, actor="urzędnik")


def test_transition_to_same_status_is_forbidden(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    with pytest.raises(InvalidTransition):
        repo.transition(case_id, CaseStatus.NOWY, actor="urzędnik", note="bez zmian")


def test_transition_to_closed_sets_response_date(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.PRZYGOTOWANA_ODPOWIEDZ)
    moved = repo.transition(case_id, CaseStatus.ODPOWIEDZ_WYSLANA, actor="urzędnik")
    assert moved.status is CaseStatus.ODPOWIEDZ_WYSLANA
    assert moved.response_date == date(2026, 3, 16)
    assert moved.urgency.value == "closed"


def test_transition_from_closed_requires_note(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.ODPOWIEDZ_WYSLANA)
    with pytest.raises(InvalidTransition):
        repo.transition(case_id, CaseStatus.PRZYGOTOWANA_ODPOWIEDZ, actor="urzędnik")
    moved = repo.transition(
        case_id,
        CaseStatus.PRZYGOTOWANA_ODPOWIEDZ,
        actor="urzędnik",
        note="Wysłano niewłaściwe pismo",
    )
    assert moved.status is CaseStatus.PRZYGOTOWANA_ODPOWIEDZ


def test_transition_missing_raises_not_found(repo: CaseRepositoryPort) -> None:
    with pytest.raises(NotFound):
        repo.transition(uuid4(), CaseStatus.ZAPYTANIA_WYSLANE, actor="urzędnik")


# ────────────────────────────────── historia ────────────────────────────────
def test_history_records_transitions_in_order(repo: CaseRepositoryPort) -> None:
    case_id = _first_with(repo, CaseStatus.NOWY)
    repo.transition(case_id, CaseStatus.ZAPYTANIA_WYSLANE, actor="urzędnik")
    repo.transition(
        case_id, CaseStatus.NOWY, actor="kierownik", note="Cofnięcie po pomyłce"
    )
    history = repo.history(case_id)
    # Oba adaptery dokładają wpis o utworzeniu sprawy (fixture'y są już
    # zarejestrowane), więc porównujemy wyłącznie zmiany stanu.
    changes = [entry for entry in history if entry.action == "status_change"]
    assert len(changes) == 2
    assert changes[0].from_value == CaseStatus.NOWY.value
    assert changes[0].to_value == CaseStatus.ZAPYTANIA_WYSLANE.value
    assert changes[1].actor == "kierownik"
    assert changes[1].note == "Cofnięcie po pomyłce"
    assert changes[0].at <= changes[1].at


def test_history_is_empty_for_unknown_case(repo: CaseRepositoryPort) -> None:
    assert repo.history(uuid4()) == []


def test_history_starts_with_creation_entry(repo: CaseRepositoryPort) -> None:
    """Nietknięta sprawa ma w historii wpis o utworzeniu, nie pustkę.

    Wcześniej tylko atrapa dokładała ten wpis — w trybie realnym panel
    historii był pusty, dopóki ktoś nie zmienił stanu sprawy.
    """
    case = repo.list()[0]
    entries = repo.history(case.id)

    assert entries
    assert entries[0].action == "created"
    assert entries[0].at.date() == case.inflow_date
    assert entries[0].note == "wniosek zarejestrowany w urzędzie"
