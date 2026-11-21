"""Przypomnienia o terminach odpowiedzi (W11).

Kotwica czasu: `DEMO_TODAY = 2026-03-16`. Z dziesięciu wniosków z `fixtures/`
przypomnieniem są trzy: po terminie (UDIP.1435.1.2026), na dziś
(UDIP.1435.2.2026) i na jutro (UDIP.1435.3.2026).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.adapters.fakes.cases import FakeCaseRepository
from app.contracts import Case, CaseStatus, Urgency
from app.core import container
from app.main import app
from app.modules.reminders.service import ReminderService, reminder_message

OVERDUE_CASE = "UDIP.1435.1.2026"
TODAY_CASE = "UDIP.1435.2.2026"
TOMORROW_CASE = "UDIP.1435.3.2026"


class _NoCasesRepository(FakeCaseRepository):
    """Repozytorium bez wniosków — do sprawdzenia stanu pustego."""

    def list(
        self,
        *,
        year: int | None = None,
        status: CaseStatus | None = None,
        q: str | None = None,
        sort: str = "deadline_asc",
    ) -> list[Case]:
        return []


class _ReversedRepository(FakeCaseRepository):
    """Zwraca wnioski w kolejności odwrotnej niż terminy.

    Serwis musi sortować sam, a nie ufać kolejności z repozytorium.
    """

    def list(
        self,
        *,
        year: int | None = None,
        status: CaseStatus | None = None,
        q: str | None = None,
        sort: str = "deadline_asc",
    ) -> list[Case]:
        rows = super().list(year=year, status=status, q=q, sort=sort)
        return list(reversed(rows))


@pytest.fixture
def empty_client() -> Iterator[TestClient]:
    """Klient API z repozytorium, które nie ma żadnego wniosku."""
    app.dependency_overrides[container.get_cases] = _NoCasesRepository
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ──────────────────────────────── endpoint ──────────────────────────────────
def test_reminders_return_overdue_today_and_tomorrow(client: TestClient) -> None:
    response = client.get("/api/reminders")

    assert response.status_code == 200
    rows = response.json()
    assert [row["case_number"] for row in rows] == [
        OVERDUE_CASE,
        TODAY_CASE,
        TOMORROW_CASE,
    ]
    assert [row["urgency"] for row in rows] == ["overdue", "today", "tomorrow"]
    assert [row["days_remaining"] for row in rows] == [-10, 0, 1]


def test_reminders_skip_closed_cases(client: TestClient) -> None:
    rows = client.get("/api/reminders").json()

    numbers = {row["case_number"] for row in rows}
    # Obie sprawy mają terminy w przeszłości, ale są już zamknięte.
    assert "UDIP.1435.7.2026" not in numbers
    assert "UDIP.1435.8.2026" not in numbers
    assert all(row["status"] != "odpowiedz_wyslana" for row in rows)


def test_reminders_skip_cases_with_distant_deadlines(client: TestClient) -> None:
    rows = client.get("/api/reminders").json()

    numbers = {row["case_number"] for row in rows}
    # Terminy za 3 dni i później nie są jeszcze przypomnieniem.
    assert "UDIP.1435.4.2026" not in numbers
    assert "UDIP.1435.5.2026" not in numbers
    assert len(rows) == 3


def test_reminders_sorted_from_most_urgent(client: TestClient) -> None:
    rows = client.get("/api/reminders").json()

    days = [row["days_remaining"] for row in rows]
    assert days == sorted(days)
    assert rows[0]["urgency"] == "overdue"
    assert rows[-1]["urgency"] == "tomorrow"


def test_reminders_carry_polish_message(client: TestClient) -> None:
    rows = client.get("/api/reminders").json()

    assert rows[0]["message"] == "Termin odpowiedzi minął 10 dni temu."
    assert rows[1]["message"] == "Termin odpowiedzi mija dziś."
    assert rows[2]["message"] == "Termin odpowiedzi mija jutro."


def test_reminders_are_computed_on_read(client: TestClient) -> None:
    """Przesunięcie terminu od razu zmienia listę — nie ma stanu w tle."""
    case_id = "c0000001-0000-4000-8000-000000000005"
    assert "UDIP.1435.5.2026" not in {
        row["case_number"] for row in client.get("/api/reminders").json()
    }

    client.patch(f"/api/cases/{case_id}", json={"deadline": "2026-03-16"})

    rows = client.get("/api/reminders").json()
    assert "UDIP.1435.5.2026" in {row["case_number"] for row in rows}


def test_reminders_empty_when_no_cases(empty_client: TestClient) -> None:
    response = empty_client.get("/api/reminders")

    assert response.status_code == 200
    assert response.json() == []


# ───────────────────────────────── serwis ───────────────────────────────────
def test_service_sorts_regardless_of_repository_order() -> None:
    reminders = ReminderService(_ReversedRepository()).list()

    assert [reminder.case_number for reminder in reminders] == [
        OVERDUE_CASE,
        TODAY_CASE,
        TOMORROW_CASE,
    ]


def test_service_returns_empty_list_for_empty_repository() -> None:
    assert ReminderService(_NoCasesRepository()).list() == []


def test_message_uses_singular_for_one_day() -> None:
    assert reminder_message(Urgency.OVERDUE, -1) == "Termin odpowiedzi minął 1 dzień temu."
    assert reminder_message(Urgency.OVERDUE, -2) == "Termin odpowiedzi minął 2 dni temu."
