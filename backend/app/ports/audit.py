"""Port dziennika audytu (WS8)."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from app.contracts import AuditEntry


class AuditPort(Protocol):
    def record(
        self,
        *,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        case_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None: ...

    def list(self, *, case_id: UUID | None = None, limit: int = 100) -> list[AuditEntry]: ...
