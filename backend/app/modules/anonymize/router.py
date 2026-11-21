"""Endpointy anonimizacji (WS6)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contracts import (
    AnonymizerMetrics,
    ApplyRequest,
    ApplyResult,
    DetectRequest,
    Span,
)
from app.core import container
from app.ports.anonymize import AnonymizerPort

router = APIRouter(tags=["anonymize"])


@router.post("/detect", response_model=list[Span])
def detect(
    req: DetectRequest, service: AnonymizerPort = Depends(container.get_anonymizer)
) -> list[Span]:
    return service.detect(req)


@router.post("/apply", response_model=ApplyResult)
def apply(
    req: ApplyRequest, service: AnonymizerPort = Depends(container.get_anonymizer)
) -> ApplyResult:
    return service.apply(req)


@router.get("/evaluate", response_model=AnonymizerMetrics)
def evaluate(
    service: AnonymizerPort = Depends(container.get_anonymizer),
) -> AnonymizerMetrics:
    return service.evaluate()
