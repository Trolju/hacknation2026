"""Model tabeli dziennika audytu (WS8).

Dziennik jest **tylko dopisywany**. Kolejność wpisów wyznacza sekwencja `seq`
(klucz główny, autoinkrementowany), a nie znacznik czasu — dwa zdarzenia w tej
samej mikrosekundzie nadal mają jednoznaczne miejsce w kolejności.

Blokada `UPDATE` i `DELETE` siedzi w wyzwalaczach SQLite, tworzonych przez
adapter `app/adapters/real/audit.py`. Dzięki temu nawet przypadkowy `UPDATE`
z konsoli bazy nie zmieni historii.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

TABLE_NAME = "audit_entries"


class AuditEntryModel(Base):
    """Wpis dziennika audytu."""

    __tablename__ = TABLE_NAME
    __table_args__ = {"sqlite_autoincrement": True}

    seq: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    case_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
