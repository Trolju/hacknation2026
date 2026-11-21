"""Testy realnego adaptera warstwy modeli (WS7) — bez sieci.

Każde żądanie HTTP przechodzi przez `httpx.MockTransport`, więc testy nie dotykają
sieci i nie potrzebują uruchomionego modelu.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.adapters.real.inference import (
    OFFLINE_MESSAGE,
    InferenceError,
    LocalEmbedding,
    OpenAICompatibleLLM,
)
from app.core import container
from app.core.errors import OfflineViolation
from app.core.settings import Settings

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Konfiguracja modeli pochodzi wyłącznie z argumentów testu, nie ze środowiska."""
    for name in (
        "OFFLINE",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "LLM_TIMEOUT_S",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_MODEL",
        "EMBEDDING_DIM",
    ):
        monkeypatch.delenv(name, raising=False)


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "llm_provider": "llamacpp",
        "llm_base_url": "http://model.local/v1",
        "llm_model": "Bielik-11B-v2.3-Instruct",
        "llm_api_key": "",
        "llm_timeout_s": 5.0,
        "offline": False,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def _llm(handler: Handler, **overrides: object) -> OpenAICompatibleLLM:
    return OpenAICompatibleLLM(
        settings=_settings(**overrides), transport=httpx.MockTransport(handler)
    )


def _embedding(handler: Handler, **overrides: object) -> LocalEmbedding:
    return LocalEmbedding(
        settings=_settings(**overrides), transport=httpx.MockTransport(handler)
    )


def _chat_response(content: str = "Odpowiedź modelu") -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def _forbidden(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"Nieoczekiwane żądanie sieciowe: {request.method} {request.url}")


# ──────────────────────────────── complete ────────────────────────────────
def test_complete_returns_content_and_sends_openai_payload() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _chat_response("Termin odpowiedzi wynosi 14 dni.")

    llm = _llm(handler)
    output = llm.complete("Ile dni na odpowiedź?", system="Jesteś urzędnikiem.")

    assert output == "Termin odpowiedzi wynosi 14 dni."
    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == "http://model.local/v1/chat/completions"
    body = json.loads(request.content)
    assert body["model"] == "Bielik-11B-v2.3-Instruct"
    assert body["stream"] is False
    assert body["messages"][0] == {"role": "system", "content": "Jesteś urzędnikiem."}
    assert body["messages"][1] == {"role": "user", "content": "Ile dni na odpowiedź?"}


def test_complete_without_api_key_sends_no_authorization_header() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _chat_response()

    _llm(handler, llm_api_key="").complete("test")

    assert "authorization" not in seen[0].headers


def test_complete_with_api_key_sends_bearer_header() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _chat_response()

    _llm(handler, llm_api_key="tajny-klucz").complete("test")

    assert seen[0].headers["authorization"] == "Bearer tajny-klucz"


def test_complete_timeout_becomes_inference_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("za wolno", request=request)

    with pytest.raises(InferenceError) as excinfo:
        _llm(handler, llm_timeout_s=0.5).complete("test")

    assert excinfo.value.status_code == 503
    assert excinfo.value.code == "inference_unavailable"
    assert "limit czasu" in excinfo.value.message
    assert "0.5" in excinfo.value.message


def test_complete_http_500_becomes_inference_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "model padł"})

    with pytest.raises(InferenceError) as excinfo:
        _llm(handler).complete("test")

    assert "500" in excinfo.value.message
    assert "model padł" in excinfo.value.message


def test_complete_connection_error_becomes_inference_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("odmowa połączenia", request=request)

    with pytest.raises(InferenceError) as excinfo:
        _llm(handler).complete("test")

    assert "Brak połączenia" in excinfo.value.message
    assert "http://model.local/v1" in excinfo.value.message


def test_complete_rejects_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    with pytest.raises(InferenceError) as excinfo:
        _llm(handler).complete("test")

    assert "choices" in excinfo.value.message


# ──────────────────────────────── offline ─────────────────────────────────
def test_offline_blocks_complete() -> None:
    llm = _llm(_forbidden, offline=True)

    with pytest.raises(OfflineViolation) as excinfo:
        llm.complete("test")

    assert excinfo.value.status_code == 503
    assert excinfo.value.message == OFFLINE_MESSAGE
    assert "offline" in excinfo.value.message.lower()


def test_offline_health_is_down_without_network_call() -> None:
    health = _llm(_forbidden, offline=True).health()

    assert health.status == "down"
    assert health.offline is True
    assert health.latency_ms is None
    assert health.message == OFFLINE_MESSAGE
    assert health.provider == "llamacpp"


def test_offline_test_returns_error_without_network_call() -> None:
    result = _llm(_forbidden, offline=True).test()

    assert result.ok is False
    assert result.output == ""
    assert result.error == OFFLINE_MESSAGE


def test_offline_models_returns_configuration_catalog_only() -> None:
    rows = _llm(_forbidden, offline=True).models()

    assert rows
    assert any(row.id == "Bielik-11B-v2.3-Instruct" for row in rows)


def test_offline_blocks_embedding() -> None:
    with pytest.raises(OfflineViolation):
        _embedding(_forbidden, offline=True).embed(["tekst"])


# ───────────────────────────────── health ─────────────────────────────────
def test_health_ok_measures_latency_with_models_endpoint() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"data": [{"id": "Bielik-11B-v2.3-Instruct"}]})

    health = _llm(handler).health()

    assert health.status == "ok"
    assert health.offline is False
    assert health.provider == "llamacpp"
    assert health.model == "Bielik-11B-v2.3-Instruct"
    assert health.latency_ms is not None
    assert health.latency_ms >= 0
    assert health.message is None
    assert str(seen[0].url) == "http://model.local/v1/models"


def test_health_degraded_when_models_endpoint_missing_but_chat_works() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(404, json={"error": "nie ma"})
        return _chat_response("ok")

    health = _llm(handler).health()

    assert health.status == "degraded"
    assert health.message is not None
    assert "listy modeli" in health.message


def test_health_down_on_server_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "awaria"})

    health = _llm(handler).health()

    assert health.status == "down"
    assert health.message is not None
    assert "500" in health.message


def test_health_down_on_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("brak odpowiedzi", request=request)

    health = _llm(handler, llm_timeout_s=0.25).health()

    assert health.status == "down"
    assert health.message is not None
    assert "limit czasu" in health.message


def test_health_down_when_provider_is_fake_but_module_is_real() -> None:
    health = _llm(_forbidden, llm_provider="fake").health()

    assert health.status == "down"
    assert health.provider == "fake"
    assert health.message is not None
    assert "LLM_PROVIDER" in health.message


# ────────────────────────────────── test ──────────────────────────────────
def test_test_returns_output_and_latency() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _chat_response("Połączenie działa.")

    result = _llm(handler).test()

    assert result.ok is True
    assert result.output == "Połączenie działa."
    assert result.error is None
    assert result.latency_ms >= 0
    assert json.loads(seen[0].content)["max_tokens"] == 32


def test_test_reports_server_error_without_raising() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "awaria modelu"})

    result = _llm(handler).test()

    assert result.ok is False
    assert result.output == ""
    assert result.error is not None
    assert "500" in result.error


def test_test_reports_missing_api_key_as_readable_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return httpx.Response(401, json={"error": {"message": "Missing bearer authentication"}})

    result = _llm(
        handler, llm_provider="openai", llm_base_url="https://api.openai.com/v1"
    ).test()

    assert result.ok is False
    assert result.error is not None
    assert "401" in result.error
    assert "Bearer" not in result.error


# ───────────────────────────────── models ─────────────────────────────────
def test_models_merges_configuration_with_server_catalog() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": "moj-model-lokalny"}]})

    rows = _llm(handler).models()
    ids = [row.id for row in rows]

    assert "moj-model-lokalny" in ids
    assert "Bielik-11B-v2.3-Instruct" in ids
    assert ids.count("Bielik-11B-v2.3-Instruct") == 1
    assert any(row.recommended for row in rows)


def test_models_falls_back_to_configuration_when_server_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "brak"})

    rows = _llm(handler).models()

    assert rows
    assert any(row.id == "Bielik-11B-v2.3-Instruct" for row in rows)


def test_models_includes_configured_model() -> None:
    rows = _llm(_forbidden, llm_model="Qwen2.5-7B-Instruct", offline=True).models()

    assert any(row.id == "Qwen2.5-7B-Instruct" for row in rows)


# ──────────────────────────────── embedding ───────────────────────────────
def test_embedding_returns_vectors_in_configured_dimension() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.4, 0.5, 0.6]},
                    {"index": 0, "embedding": [0.1, 0.2, 0.3]},
                ]
            },
        )

    embedding = _embedding(handler, embedding_dim=3)
    vectors = embedding.embed(["ala ma kota", "kot ma alę"])

    assert embedding.dim == 3
    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    body = json.loads(seen[0].content)
    assert body["model"] == "BAAI/bge-m3"
    assert body["input"] == ["ala ma kota", "kot ma alę"]
    assert str(seen[0].url) == "http://model.local/v1/embeddings"


def test_embedding_fits_vector_to_configured_dimension() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"index": 0, "embedding": [1.0, 2.0]}]})

    assert _embedding(handler, embedding_dim=4).embed(["tekst"]) == [[1.0, 2.0, 0.0, 0.0]]


def test_embedding_truncates_too_long_vector() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"data": [{"index": 0, "embedding": [1.0, 2.0, 3.0, 4.0]}]}
        )

    assert _embedding(handler, embedding_dim=2).embed(["tekst"]) == [[1.0, 2.0]]


def test_embedding_empty_input_skips_network() -> None:
    assert _embedding(_forbidden).embed([]) == []


def test_embedding_timeout_becomes_inference_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("za wolno", request=request)

    with pytest.raises(InferenceError) as excinfo:
        _embedding(handler).embed(["tekst"])

    assert "limit czasu" in excinfo.value.message


def test_embedding_rejects_malformed_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    with pytest.raises(InferenceError) as excinfo:
        _embedding(handler).embed(["tekst"])

    assert "wektorów" in excinfo.value.message


# ──────────────────────────── domyślne dostawcy ───────────────────────────
@pytest.mark.parametrize(
    ("provider", "expected_url", "expected_model"),
    [
        ("llamacpp", "http://localhost:8080/v1/chat/completions", "Bielik-11B-v2.3-Instruct"),
        ("ollama", "http://localhost:11434/v1/chat/completions", "Bielik-11B-v2.3-Instruct"),
        ("openai", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    ],
)
def test_provider_defaults_differ_in_port_and_model(
    provider: str, expected_url: str, expected_model: str
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _chat_response()

    llm = OpenAICompatibleLLM(
        settings=Settings(llm_provider=provider),  # type: ignore[arg-type]
        transport=httpx.MockTransport(handler),
    )
    llm.complete("test")

    assert str(seen[0].url) == expected_url
    assert json.loads(seen[0].content)["model"] == expected_model


# ──────────────────────────────── kontener ────────────────────────────────
def test_container_resolves_real_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODULE_MODE_INFERENCE", "real")
    monkeypatch.setenv("MODULE_MODE_INFERENCE_EMBEDDING", "real")
    container.reset()

    assert isinstance(container.get_llm(), OpenAICompatibleLLM)
    assert isinstance(container.get_embedding(), LocalEmbedding)


# ──────────────────────────────── przez API ───────────────────────────────
def test_api_health_reports_down_in_offline_mode(client: TestClient) -> None:
    container._instances["inference"] = OpenAICompatibleLLM(settings=_settings(offline=True))

    response = client.get("/api/inference/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "down"
    assert body["offline"] is True
    assert body["message"] == OFFLINE_MESSAGE


def test_api_test_returns_result_instead_of_error_in_offline_mode(
    client: TestClient,
) -> None:
    container._instances["inference"] = OpenAICompatibleLLM(settings=_settings(offline=True))

    response = client.post("/api/inference/test")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["error"] == OFFLINE_MESSAGE


def test_api_health_does_not_return_500_when_server_fails(client: TestClient) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "awaria"})

    container._instances["inference"] = _llm(handler)

    response = client.get("/api/inference/health")

    assert response.status_code == 200
    assert response.json()["status"] == "down"


# ──────────────────────────── dostawca Mistral ─────────────────────────────
def _mistral_settings(**overrides: object) -> Settings:
    """Konfiguracja bez jawnych `llm_base_url` / `llm_model` — działa preset."""
    base: dict[str, object] = {
        "llm_provider": "mistral",
        "llm_api_key": "test-key",
        "llm_timeout_s": 5.0,
        "offline": False,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_mistral_preset_sets_base_url_and_model() -> None:
    llm = OpenAICompatibleLLM(settings=_mistral_settings())

    assert llm._base_url() == "https://api.mistral.ai/v1"
    assert llm._model() == "mistral-small-latest"


def test_mistral_explicit_configuration_wins_over_preset() -> None:
    llm = OpenAICompatibleLLM(
        settings=_mistral_settings(
            llm_base_url="http://model.local/v1",
            llm_model="open-mistral-nemo",
        )
    )

    assert llm._base_url() == "http://model.local/v1"
    assert llm._model() == "open-mistral-nemo"


def test_mistral_sends_bearer_token() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("Authorization", "")
        return _chat_response()

    llm = OpenAICompatibleLLM(
        settings=_mistral_settings(), transport=httpx.MockTransport(handler)
    )

    assert llm.complete("Ile dni na odpowiedź?") == "Odpowiedź modelu"
    assert seen["url"] == "https://api.mistral.ai/v1/chat/completions"
    assert seen["auth"] == "Bearer test-key"


def test_mistral_health_reports_provider() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"id": "mistral-small-latest"}]})

    llm = OpenAICompatibleLLM(
        settings=_mistral_settings(), transport=httpx.MockTransport(handler)
    )

    health = llm.health()

    assert health.provider == "mistral"
    assert health.status == "ok"


def test_katalog_zawiera_modele_mistrala() -> None:
    llm = OpenAICompatibleLLM(settings=_mistral_settings(offline=True))

    ids = {row.id for row in llm.models()}

    assert "mistral-small-latest" in ids
    assert "open-mistral-nemo" in ids
