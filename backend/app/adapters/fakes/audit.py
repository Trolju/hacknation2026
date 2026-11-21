"""Atrapa dziennika audytowego — zapis w pamięci procesu."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.contracts import AuditEntry


class FakeAuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def record(
        self,
        *,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        case_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._entries.append(
            AuditEntry(
                id=uuid4(),
                at=datetime.now(UTC),
                actor=actor,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                case_id=case_id,
                payload=payload or {},
            )
        )

    def list(self, *, case_id: UUID | None = None, limit: int = 100) -> list[AuditEntry]:
        rows = self._entries
        if case_id is not None:
            rows = [e for e in rows if e.case_id == case_id]
        return list(reversed(rows))[:limit]
