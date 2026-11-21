"""Pola wyliczane — wspólne dla atrap i implementacji.

Trzymane w jednym miejscu, żeby fake i real nie rozjechały się w interpretacji
urgency (W2) ani dni do terminu (W1).
"""

from __future__ import annotations

from datetime import date

from app.contracts import CaseStatus, Urgency
from app.core.clock import today


def days_remaining(deadline: date, *, ref: date | None = None) -> int:
    return (deadline - (ref or today())).days


def urgency_for(status: CaseStatus, days: int) -> Urgency:
    if status is CaseStatus.ODPOWIEDZ_WYSLANA:
        return Urgency.CLOSED
    if days < 0:
        return Urgency.OVERDUE
    if days == 0:
        return Urgency.TODAY
    if days == 1:
        return Urgency.TOMORROW
    if days <= 3:
        return Urgency.SOON
    return Urgency.NORMAL


def compute(status: CaseStatus, deadline: date, *, ref: date | None = None) -> tuple[int, Urgency]:
    days = days_remaining(deadline, ref=ref)
    return days, urgency_for(status, days)
