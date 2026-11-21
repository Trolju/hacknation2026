"""Port routingu wydziałowego (WS4)."""

from __future__ import annotations

from typing import Protocol

from app.contracts import (
    Department,
    DepartmentSuggestion,
    GeneratedLetter,
    InquiryRequest,
    SuggestRequest,
)


class DepartmentRouterPort(Protocol):
    def departments(self) -> list[Department]: ...

    def suggest(self, req: SuggestRequest) -> list[DepartmentSuggestion]: ...

    def inquiry(self, req: InquiryRequest) -> GeneratedLetter: ...
