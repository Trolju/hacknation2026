"""DTO przypomnień o terminach odpowiedzi (W11).

Przypomnienie nie jest nowym bytem domenowym, tylko widokiem pochodnym wniosku:
powstaje z pól wyliczanych `days_remaining` i `urgency`. Dlatego model mieszka
w module, a nie w zamrożonym `app/contracts.py` — kontrakt API wniosków
zostaje bez zmian.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.contracts import CaseStatus, Urgency


class Reminder(BaseModel):
    """Pojedyncze przypomnienie o terminie odpowiedzi na wniosek."""

    model_config = ConfigDict(from_attributes=True)

    case_id: UUID
    case_number: str
    subject: str
    deadline: date
    #: Dni do terminu przepisane z wniosku — ujemne znaczą „po terminie”.
    days_remaining: int
    urgency: Urgency
    status: CaseStatus
    handler_initials: str = ""
    #: Gotowy tekst przypomnienia po polsku — frontend nie musi go składać.
    message: str
