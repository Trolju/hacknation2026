"""Modele SQLAlchemy 2.0 dla wniosków (WS1).

Tabele `cases` i `case_history`. Pola wyliczane (`days_remaining`, `urgency`,
`year`) nie mają swoich kolumn — liczy je `app.core.derive` przy każdym odczycie,
więc nie rozjeżdżają się z upływem czasu.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class CaseRow(Base):
    """Rekord kalendarza — jeden wniosek o udostępnienie informacji publicznej."""

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str] = mapped_column(String(200))
    inflow_date: Mapped[date] = mapped_column(Date, index=True)
    deadline: Mapped[date] = mapped_column(Date, index=True)
    response_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    handler_initials: Mapped[str] = mapped_column(String(8), default="")
    status: Mapped[str] = mapped_column(String(32), index=True)
    applicant_type: Mapped[str] = mapped_column(String(32), default="inne")
    source_document_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    #: Łączne przedłużenie terminu w kwerendzie, w dniach (W12).
    kwerenda_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    document_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)

    history: Mapped[list[CaseHistoryRow]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseHistoryRow.at",
    )


class CaseHistoryRow(Base):
    """Wpis historii zmian sprawy — jedno zdarzenie (utworzenie, zmiana pola, statusu)."""

    __tablename__ = "case_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    at: Mapped[datetime] = mapped_column(DateTime, index=True)
    actor: Mapped[str] = mapped_column(String(64), default="urzędnik")
    action: Mapped[str] = mapped_column(String(32))
    from_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    case: Mapped[CaseRow] = relationship(back_populates="history")
