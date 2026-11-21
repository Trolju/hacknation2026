"""Port anonimizacji (WS6)."""

from __future__ import annotations

from typing import Protocol

from app.contracts import (
    AnonymizerMetrics,
    ApplyRequest,
    ApplyResult,
    DetectRequest,
    Span,
)


class AnonymizerPort(Protocol):
    def detect(self, req: DetectRequest) -> list[Span]: ...

    def apply(self, req: ApplyRequest) -> ApplyResult: ...

    def evaluate(self) -> AnonymizerMetrics: ...
