"""Porty warstwy modeli (WS7).

`LLMPort` i `EmbeddingPort` są jedynym miejscem, w którym aplikacja dotyka
modelu. Adaptery: fake (testy), openai-compatible (dev), llamacpp/ollama (lokalnie).
"""

from __future__ import annotations

from typing import Protocol

from app.contracts import InferenceHealth, InferenceTestResult, ModelInfo


class LLMPort(Protocol):
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str: ...

    def health(self) -> InferenceHealth: ...

    def models(self) -> list[ModelInfo]: ...

    def test(self) -> InferenceTestResult: ...


class EmbeddingPort(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    def dim(self) -> int: ...
