"""Port generatora odpowiedzi (WS5)."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.contracts import Draft, DraftPatch, DraftRequest


class DraftingPort(Protocol):
    def draft(self, req: DraftRequest) -> Draft: ...

    def get(self, case_id: UUID) -> Draft: ...

    def update(self, draft_id: UUID, patch: DraftPatch) -> Draft: ...

    def export(self, draft_id: UUID, *, fmt: str, anonymized: bool) -> tuple[bytes, str]:
        """Zwraca (bajty, nazwa pliku)."""
        ...

    def redactions(self, draft_id: UUID) -> int:
        """Ile fragmentów usunęłaby anonimizacja — 0, gdy nie ma czego ukrywać."""
        ...
