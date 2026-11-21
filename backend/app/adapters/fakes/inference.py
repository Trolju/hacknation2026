"""Atrapa warstwy modelowej — deterministyczne odpowiedzi bez sieci."""

from __future__ import annotations

import hashlib
import time

from app.contracts import InferenceHealth, InferenceTestResult, ModelInfo

_DIM = 256

_CATALOG: list[ModelInfo] = [
    ModelInfo(
        id="Bielik-11B-v2.3-Instruct",
        label="Bielik 11B v2.3 Instruct (Q4_K_M)",
        provider="llamacpp",
        local=True,
        size_gb=6.7,
        recommended=True,
    ),
    ModelInfo(
        id="Qwen2.5-7B-Instruct",
        label="Qwen2.5 7B Instruct (Q4_K_M)",
        provider="llamacpp",
        local=True,
        size_gb=4.7,
    ),
    ModelInfo(
        id="fake-instruct",
        label="Atrapa modelu (testy)",
        provider="fake",
        local=True,
        size_gb=0.0,
    ),
]


class FakeLLM:
    """Zwraca przewidywalny tekst; pozwala testować przepływ bez modelu."""

    def __init__(self, model: str = "fake-instruct") -> None:
        self._model = model

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8]
        return (
            "[atrapa modelu] Odpowiedź wygenerowana deterministycznie. "
            f"Skrót zapytania: {digest}, limit tokenów: {max_tokens or 'brak'}, "
            f"temperatura: {temperature if temperature is not None else 'domyślna'}."
        )

    def health(self) -> InferenceHealth:
        return InferenceHealth(
            provider="fake",
            model=self._model,
            status="ok",
            offline=True,
            latency_ms=0.0,
            message="Tryb atrapy — model nie jest wywoływany.",
        )

    def models(self) -> list[ModelInfo]:
        return list(_CATALOG)

    def test(self) -> InferenceTestResult:
        started = time.perf_counter()
        output = self.complete("Test połączenia z modelem.", max_tokens=16)
        return InferenceTestResult(
            ok=True,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            output=output,
        )


class FakeEmbedding:
    """Wektory worka słów — wystarczające do testów podobieństwa."""

    def __init__(self, dim: int = _DIM) -> None:
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self._dim
            for token in text.lower().split():
                idx = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self._dim
                vec[idx] += 1.0
            norm = sum(v * v for v in vec) ** 0.5 or 1.0
            out.append([round(v / norm, 6) for v in vec])
        return out
