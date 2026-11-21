"""Przypomnienia o zbliżających się terminach odpowiedzi (W11).

Automatyzacja jest „przy odczycie”: lista powstaje w momencie zapytania
z pól wyliczanych wniosku (`days_remaining`, `urgency`), więc nie ma schedulera,
wątku w tle ani własnego liczenia terminów. Dzięki temu wynik jest w pełni
deterministyczny i zgodny z `DEMO_TODAY`.
"""

from __future__ import annotations

import builtins

from app.contracts import Case, Urgency
from app.modules.reminders.models import Reminder
from app.ports.cases import CaseRepositoryPort

#: Pilności, o których urzędnik dostaje przypomnienie. `soon`, `normal`
#: i `closed` świadomie pomijamy — to nie są terminy wymagające reakcji dziś.
REMINDER_URGENCIES: frozenset[Urgency] = frozenset(
    {Urgency.OVERDUE, Urgency.TODAY, Urgency.TOMORROW}
)


def _days_label(days: int) -> str:
    """Odmiana rzeczownika „dzień” po liczbie."""
    return "1 dzień" if days == 1 else f"{days} dni"


def reminder_message(urgency: Urgency, days_remaining: int) -> str:
    """Tekst przypomnienia gotowy do pokazania urzędnikowi."""
    if urgency is Urgency.OVERDUE:
        return f"Termin odpowiedzi minął {_days_label(abs(days_remaining))} temu."
    if urgency is Urgency.TODAY:
        return "Termin odpowiedzi mija dziś."
    if urgency is Urgency.TOMORROW:
        return "Termin odpowiedzi mija jutro."
    return f"Termin odpowiedzi za {_days_label(days_remaining)}."


def to_reminder(case: Case) -> Reminder:
    """Przepisuje wniosek na przypomnienie — bez przeliczania terminu."""
    return Reminder(
        case_id=case.id,
        case_number=case.case_number,
        subject=case.subject,
        deadline=case.deadline,
        days_remaining=case.days_remaining,
        urgency=case.urgency,
        status=case.status,
        handler_initials=case.handler_initials,
        message=reminder_message(case.urgency, case.days_remaining),
    )


def sort_key(reminder: Reminder) -> tuple[int, str]:
    """Od najpilniejszych: po terminie, na dziś, na jutro; remis po numerze."""
    return (reminder.days_remaining, reminder.case_number)


class ReminderService:
    """Buduje listę przypomnień z repozytorium wniosków."""

    def __init__(self, repo: CaseRepositoryPort) -> None:
        self._repo = repo

    def list(self) -> builtins.list[Reminder]:
        cases = self._repo.list(sort="deadline_asc")
        reminders = [
            to_reminder(case) for case in cases if case.urgency in REMINDER_URGENCIES
        ]
        return sorted(reminders, key=sort_key)
