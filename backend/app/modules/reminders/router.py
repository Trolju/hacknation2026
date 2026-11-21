"""Endpoint przypomnień o terminach odpowiedzi (W11).

Router tylko deleguje: listę buduje `service.py` z pól wyliczanych wniosku,
a repozytorium wybiera kontener. Moduł nie ma własnego adaptera — korzysta
z `CaseRepositoryPort`, więc działa identycznie na atrapie i na SQL.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core import container
from app.modules.reminders.models import Reminder
from app.modules.reminders.service import ReminderService
from app.ports.cases import CaseRepositoryPort

router = APIRouter(tags=["reminders"])


@router.get("", response_model=list[Reminder])
def list_reminders(
    repo: CaseRepositoryPort = Depends(container.get_cases),
) -> list[Reminder]:
    """Wnioski po terminie, na dziś i na jutro — od najpilniejszych."""
    return ReminderService(repo).list()
