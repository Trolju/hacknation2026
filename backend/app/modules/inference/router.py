"""Endpointy warstwy modeli (WS7)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contracts import InferenceHealth, InferenceTestResult, ModelInfo
from app.core import container
from app.ports.inference import LLMPort

router = APIRouter(tags=["inference"])


@router.get("/health", response_model=InferenceHealth)
def health(llm: LLMPort = Depends(container.get_llm)) -> InferenceHealth:
    return llm.health()


@router.get("/models", response_model=list[ModelInfo])
def models(llm: LLMPort = Depends(container.get_llm)) -> list[ModelInfo]:
    return llm.models()


@router.post("/test", response_model=InferenceTestResult)
def test(llm: LLMPort = Depends(container.get_llm)) -> InferenceTestResult:
    return llm.test()
