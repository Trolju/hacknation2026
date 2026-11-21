"""Realna warstwa modeli językowych (WS7).

llama.cpp, Ollama i OpenAI mówią tym samym protokołem OpenAI, więc obsługuje je
jeden adapter: `POST /chat/completions`, `POST /embeddings`, `GET /models`.
Różnice sprowadzają się do domyślnego adresu i domyślnej nazwy modelu.

Tryb offline (`OFFLINE=true`) blokuje każde wyjście do sieci: `complete()` i
`embed()` rzucają `OfflineViolation`, a `health()` raportuje `down` bez próby
połączenia. Błędy sieci i timeouty nigdy nie wychodzą jako wyjątek 500 —
`health()` i `test()` zamieniają je na `status` i czytelny komunikat po polsku.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Final, Literal

import httpx
import structlog

from app.contracts import InferenceHealth, InferenceTestResult, ModelInfo
from app.core.errors import AppError, OfflineViolation
from app.core.settings import Settings
from app.core.settings import settings as default_settings

log = structlog.get_logger(__name__)

ProviderName = Literal["fake", "openai", "mistral", "llamacpp", "ollama"]

OFFLINE_MESSAGE: Final[str] = (
    "Tryb offline jest włączony — wywołania modeli językowych są zablokowane. "
    "Aby korzystać z modelu, ustaw OFFLINE=false i uruchom lokalny serwer modelu."
)

FAKE_PROVIDER_MESSAGE: Final[str] = (
    "Wybrano atrapę modelu (LLM_PROVIDER=fake), a moduł inference działa w trybie "
    "realnym. Ustaw LLM_PROVIDER na llamacpp, ollama albo openai."
)

# Health check nie może wisieć tyle, ile pełne generowanie odpowiedzi.
_HEALTH_TIMEOUT_CAP_S: Final[float] = 10.0
_TEST_PROMPT: Final[str] = "Odpowiedz jednym krótkim zdaniem: test połączenia."
_TEST_MAX_TOKENS: Final[int] = 32
_TEST_OUTPUT_LIMIT: Final[int] = 400
_ERROR_BODY_LIMIT: Final[int] = 200


class InferenceError(AppError):
    """Model lub serwer modelu jest niedostępny — 503 z komunikatem po polsku."""

    status_code = 503
    code = "inference_unavailable"


@dataclass(frozen=True)
class _ProviderDefaults:
    """Domyślne wartości dla dostawcy, gdy konfiguracja ich nie nadpisuje."""

    base_url: str
    model: str
    local: bool


_PROVIDERS: Final[dict[str, _ProviderDefaults]] = {
    "llamacpp": _ProviderDefaults(
        base_url="http://localhost:8080/v1",
        model="Bielik-11B-v2.3-Instruct",
        local=True,
    ),
    "ollama": _ProviderDefaults(
        base_url="http://localhost:11434/v1",
        model="Bielik-11B-v2.3-Instruct",
        local=True,
    ),
    "openai": _ProviderDefaults(
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        local=False,
    ),
    # Mistral La Plateforme mówi protokołem OpenAI, więc ten sam adapter
    # obsługuje chmurę i model lokalny — zmienia się tylko `LLM_BASE_URL`.
    # Domyślnie `mistral-small-latest`, bo Mistral Small 3.1 24B ma otwarte
    # wagi (Apache 2.0): ten sam model da się uruchomić w urzędzie bez sieci.
    "mistral": _ProviderDefaults(
        base_url="https://api.mistral.ai/v1",
        model="mistral-small-latest",
        local=False,
    ),
}

# Katalog modeli rekomendowanych dla urzędu — niezależny od tego, co odpowie serwer.
_CATALOG: Final[tuple[ModelInfo, ...]] = (
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
        id="gpt-4o-mini",
        label="OpenAI GPT-4o mini (chmura)",
        provider="openai",
        local=False,
    ),
    ModelInfo(
        id="mistral-small-latest",
        label="Mistral Small 3.1 24B (chmura, wagi otwarte)",
        provider="mistral",
        local=False,
        size_gb=14.3,
    ),
    ModelInfo(
        id="open-mistral-nemo",
        label="Mistral NeMo 12B (chmura, wagi otwarte)",
        provider="mistral",
        local=False,
        size_gb=7.1,
    ),
)


# ─────────────────────────────── pomocnicze ────────────────────────────────
def _resolve_base_url(settings: Settings, provider: ProviderName) -> str:
    """Adres serwera: jawna konfiguracja wygrywa, inaczej domyślna dla dostawcy."""
    if "llm_base_url" in settings.model_fields_set and settings.llm_base_url.strip():
        return settings.llm_base_url.strip().rstrip("/")
    return _PROVIDERS.get(provider, _PROVIDERS["ollama"]).base_url


def _resolve_model(settings: Settings, provider: ProviderName) -> str:
    """Nazwa modelu: jawna konfiguracja wygrywa, inaczej domyślna dla dostawcy."""
    if "llm_model" in settings.model_fields_set and settings.llm_model.strip():
        return settings.llm_model.strip()
    return _PROVIDERS.get(provider, _PROVIDERS["ollama"]).model


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)


def _message(exc: BaseException) -> str:
    """Czytelny opis błędu — bez śladów stosu i bez sekretów."""
    if isinstance(exc, AppError):
        return exc.message
    return f"Nieoczekiwany błąd warstwy modeli: {exc}"


def _snippet(response: httpx.Response) -> str:
    text = " ".join(response.text.split())
    return text[:_ERROR_BODY_LIMIT] if text else "brak treści odpowiedzi"


def _extract_content(data: Any) -> str:
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise InferenceError(
            "Odpowiedź serwera modelu nie zawiera treści "
            "(brak pola choices[0].message.content)."
        ) from exc
    if not isinstance(content, str) or not content.strip():
        raise InferenceError("Model zwrócił pustą odpowiedź.")
    return content.strip()


def _server_model_ids(data: Any) -> list[str]:
    """Wyciąga identyfikatory modeli z odpowiedzi `GET /models`."""
    if not isinstance(data, dict):
        return []
    raw = data.get("data")
    if not isinstance(raw, list):
        return []
    ids: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            model_id = item.get("id")
            if isinstance(model_id, str) and model_id.strip():
                ids.append(model_id.strip())
    return ids


def _extract_embeddings(data: Any) -> list[list[float]]:
    if not isinstance(data, dict):
        raise InferenceError("Serwer embeddingów zwrócił odpowiedź w nieoczekiwanym formacie.")
    raw = data.get("data")
    if not isinstance(raw, list) or not raw:
        raise InferenceError(
            "Odpowiedź serwera embeddingów nie zawiera wektorów (brak pola data)."
        )
    ordered = sorted(
        raw, key=lambda item: item.get("index", 0) if isinstance(item, dict) else 0
    )
    vectors: list[list[float]] = []
    for item in ordered:
        embedding = item.get("embedding") if isinstance(item, dict) else None
        if not isinstance(embedding, list) or not embedding:
            raise InferenceError("Odpowiedź serwera embeddingów ma niepoprawny format wektora.")
        try:
            vectors.append([float(value) for value in embedding])
        except (TypeError, ValueError) as exc:
            raise InferenceError(
                "Wektor z serwera embeddingów zawiera wartości, które nie są liczbami."
            ) from exc
    return vectors


# ─────────────────────────────── klient HTTP ───────────────────────────────
class _OpenAICompatibleClient:
    """Wspólna obsługa protokołu OpenAI: adres, nagłówki, błędy, timeouty."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._settings = settings if settings is not None else default_settings
        self._transport = transport

    # ── konfiguracja ──
    def _provider(self) -> ProviderName:
        return self._settings.llm_provider

    def _defaults(self) -> _ProviderDefaults:
        return _PROVIDERS.get(self._provider(), _PROVIDERS["ollama"])

    def _base_url(self) -> str:
        return _resolve_base_url(self._settings, self._provider())

    def _model(self) -> str:
        return _resolve_model(self._settings, self._provider())

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        api_key = self._settings.llm_api_key.strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _health_timeout(self) -> float:
        return min(self._settings.llm_timeout_s, _HEALTH_TIMEOUT_CAP_S)

    def _url(self, path: str) -> str:
        return f"{self._base_url()}/{path.lstrip('/')}"

    def _ensure_online(self) -> None:
        if self._settings.offline:
            raise OfflineViolation(OFFLINE_MESSAGE)

    # ── transport ──
    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        limit = self._settings.llm_timeout_s if timeout is None else timeout
        url = self._url(path)
        try:
            with httpx.Client(
                timeout=httpx.Timeout(limit),
                transport=self._transport,
                headers=self._headers(),
            ) as client:
                response = client.request(method, url, json=payload)
        except httpx.TimeoutException as exc:
            raise InferenceError(
                f"Przekroczono limit czasu {limit:g} s — serwer modelu pod adresem "
                f"{self._base_url()} nie odpowiedział."
            ) from exc
        except httpx.HTTPError as exc:
            raise InferenceError(
                f"Brak połączenia z serwerem modelu pod adresem {self._base_url()}: {exc}."
            ) from exc

        if response.status_code >= 400:
            raise InferenceError(
                f"Serwer modelu zwrócił błąd HTTP {response.status_code}: {_snippet(response)}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise InferenceError(
                "Serwer modelu zwrócił odpowiedź, której nie da się odczytać (niepoprawny JSON)."
            ) from exc


# ──────────────────────────────── adaptery ────────────────────────────────
class OpenAICompatibleLLM(_OpenAICompatibleClient):
    """`LLMPort` po protokole OpenAI — llama.cpp, Ollama albo OpenAI."""

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        self._ensure_online()
        if self._provider() == "fake":
            raise InferenceError(FAKE_PROVIDER_MESSAGE)

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = self._request_json(
            "POST",
            "/chat/completions",
            payload={
                "model": self._model(),
                "messages": messages,
                "max_tokens": (
                    max_tokens if max_tokens is not None else self._settings.llm_max_tokens
                ),
                "temperature": (
                    self._settings.llm_temperature if temperature is None else temperature
                ),
                "stream": False,
            },
        )
        return _extract_content(data)

    def health(self) -> InferenceHealth:
        provider = self._provider()
        model = self._model()

        if self._settings.offline:
            return InferenceHealth(
                provider=provider,
                model=model,
                status="down",
                offline=True,
                latency_ms=None,
                message=OFFLINE_MESSAGE,
            )
        if provider == "fake":
            return InferenceHealth(
                provider=provider,
                model=model,
                status="down",
                offline=False,
                latency_ms=None,
                message=FAKE_PROVIDER_MESSAGE,
            )

        started = time.perf_counter()
        try:
            self._probe_models()
        except Exception as models_error:  # noqa: BLE001 - health nigdy nie zwraca 500
            try:
                self._probe_chat()
            except Exception as chat_error:  # noqa: BLE001 - jak wyżej
                log.warning(
                    "inference_health_down", provider=provider, error=_message(chat_error)
                )
                return InferenceHealth(
                    provider=provider,
                    model=model,
                    status="down",
                    offline=False,
                    latency_ms=_elapsed_ms(started),
                    message=_message(chat_error),
                )
            log.info(
                "inference_health_degraded", provider=provider, error=_message(models_error)
            )
            return InferenceHealth(
                provider=provider,
                model=model,
                status="degraded",
                offline=False,
                latency_ms=_elapsed_ms(started),
                message=(
                    "Serwer modelu odpowiada, ale nie udostępnia listy modeli "
                    f"({_message(models_error)})."
                ),
            )

        return InferenceHealth(
            provider=provider,
            model=model,
            status="ok",
            offline=False,
            latency_ms=_elapsed_ms(started),
            message=None,
        )

    def models(self) -> list[ModelInfo]:
        catalog = self._catalog()
        if self._settings.offline or self._provider() == "fake":
            return catalog
        try:
            data = self._request_json("GET", "/models", timeout=self._health_timeout())
        except Exception as exc:  # noqa: BLE001 - katalog z konfiguracji wystarczy
            log.info(
                "inference_models_unavailable", provider=self._provider(), error=_message(exc)
            )
            return catalog

        known = {row.id for row in catalog}
        local = self._defaults().local
        for model_id in _server_model_ids(data):
            if model_id not in known:
                known.add(model_id)
                catalog.append(
                    ModelInfo(
                        id=model_id,
                        label=model_id,
                        provider=self._provider(),
                        local=local,
                    )
                )
        return catalog

    def test(self) -> InferenceTestResult:
        if self._settings.offline:
            return InferenceTestResult(
                ok=False, latency_ms=0.0, output="", error=OFFLINE_MESSAGE
            )
        if self._provider() == "fake":
            return InferenceTestResult(
                ok=False, latency_ms=0.0, output="", error=FAKE_PROVIDER_MESSAGE
            )

        started = time.perf_counter()
        try:
            output = self.complete(
                _TEST_PROMPT, max_tokens=_TEST_MAX_TOKENS, temperature=0.0
            )
        except Exception as exc:  # noqa: BLE001 - test nigdy nie zwraca 500
            log.warning(
                "inference_test_failed", provider=self._provider(), error=_message(exc)
            )
            return InferenceTestResult(
                ok=False,
                latency_ms=_elapsed_ms(started),
                output="",
                error=_message(exc),
            )
        return InferenceTestResult(
            ok=True,
            latency_ms=_elapsed_ms(started),
            output=output[:_TEST_OUTPUT_LIMIT],
        )

    # ── wewnętrzne ──
    def _catalog(self) -> list[ModelInfo]:
        active = self._model()
        rows: list[ModelInfo] = []
        if all(entry.id != active for entry in _CATALOG):
            rows.append(
                ModelInfo(
                    id=active,
                    label=f"{active} (skonfigurowany)",
                    provider=self._provider(),
                    local=self._defaults().local,
                )
            )
        rows.extend(entry.model_copy() for entry in _CATALOG)
        return rows

    def _probe_models(self) -> None:
        self._request_json("GET", "/models", timeout=self._health_timeout())

    def _probe_chat(self) -> None:
        data = self._request_json(
            "POST",
            "/chat/completions",
            payload={
                "model": self._model(),
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0.0,
                "stream": False,
            },
            timeout=self._health_timeout(),
        )
        if not isinstance(data, dict) or "choices" not in data:
            raise InferenceError(
                "Serwer modelu odpowiedział, ale odpowiedź nie ma formatu OpenAI "
                "(brak pola choices)."
            )


class LocalEmbedding(_OpenAICompatibleClient):
    """`EmbeddingPort` po protokole OpenAI (`POST /embeddings`)."""

    def _provider(self) -> ProviderName:
        if self._settings.embedding_provider == "openai":
            return "openai"
        return self._settings.llm_provider

    @property
    def dim(self) -> int:
        return self._settings.embedding_dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self._ensure_online()

        data = self._request_json(
            "POST",
            "/embeddings",
            payload={"model": self._settings.embedding_model, "input": list(texts)},
        )
        vectors = _extract_embeddings(data)
        if len(vectors) != len(texts):
            raise InferenceError(
                f"Serwer embeddingów zwrócił {len(vectors)} wektorów dla {len(texts)} tekstów."
            )
        return [self._fit_dim(vector) for vector in vectors]

    def _fit_dim(self, vector: list[float]) -> list[float]:
        """Dopasowuje wektor do `EMBEDDING_DIM`, żeby port zawsze trzymał wymiar."""
        dim = self.dim
        if len(vector) == dim:
            return vector
        log.warning("embedding_dim_mismatch", expected=dim, received=len(vector))
        if len(vector) > dim:
            return vector[:dim]
        return [*vector, *([0.0] * (dim - len(vector)))]
