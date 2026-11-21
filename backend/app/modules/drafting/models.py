"""Tabele generatora odpowiedzi (WS5): projekty i historia wersji.

Modele są odkrywane przez `app.core.db.create_all()` — wystarczy plik
`models.py` w katalogu modułu, bez wpisywania się do rejestru.

`drafts` trzyma zawsze najnowszą wersję projektu (jeden projekt na sprawę),
`draft_history` — pełne migawki kolejnych wersji wraz z autorem i powodem
zmiany. Dzięki migawkom urzędnik może wrócić do treści sprzed korekty, a my
nie musimy liczyć różnic przy każdym odczycie.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class DraftRow(Base):
    """Aktualna wersja projektu odpowiedzi dla sprawy."""

    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(36), index=True, unique=True)
    title: Mapped[str] = mapped_column(String(512))
    body: Mapped[str] = mapped_column(Text, default="")
    citations: Mapped[str] = mapped_column(Text, default="[]")
    unsupported: Mapped[str] = mapped_column(Text, default="[]")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class DraftHistoryRow(Base):
    """Migawka wersji projektu — kto, kiedy i jaka treść."""

    __tablename__ = "draft_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    draft_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("drafts.id", ondelete="CASCADE"), index=True
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(32))
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(512))
    body: Mapped[str] = mapped_column(Text, default="")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
