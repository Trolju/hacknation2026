"""Port repozytorium wniosków (WS1)."""

from __future__ import annotations

import builtins
from typing import Protocol
from uuid import UUID

from app.contracts import (
    Case,
    CaseCreate,
    CaseDetail,
    CasePatch,
    CaseStatus,
    HistoryEntry,
)


class CaseRepositoryPort(Protocol):
    def list(
        self,
        *,
        year: int | None = None,
        status: CaseStatus | None = None,
        q: str | None = None,
        sort: str = "inflow_asc",
    ) -> builtins.list[Case]: ...

    def years(self) -> builtins.list[int]: ...

    def get(self, case_id: UUID) -> CaseDetail: ...

    def create(self, data: CaseCreate) -> Case: ...

    def update(self, case_id: UUID, patch: CasePatch) -> Case: ...

    def transition(
        self,
        case_id: UUID,
        to: CaseStatus,
        *,
        actor: str,
        note: str | None = None,
        kwerenda_days: int | None = None,
    ) -> Case:
        """Zmienia stan sprawy.

        `kwerenda_days` ma sens tylko przy przejściu do `kwerenda` — przesuwa
        termin odpowiedzi o podaną liczbę dni i zapisuje ją na sprawie.
        """
        ...

    def history(self, case_id: UUID) -> builtins.list[HistoryEntry]: ...
