"""Kontrakt generatora z modelem w formacie, jaki realnie zwraca Mistral.

Raport z testów wykazał, że **żaden test w repozytorium nie dotykał modelu**:
`test_inference_real.py` używa `MockTransport`, a `test_e2e_flow.py` deklaruje
wprost, że warstwa `inference` nie znajduje serwera i generator schodzi do
szablonu. Dlatego dwa defekty widoczne tylko na żywym modelu przeszły przez
478 testów niezauważone:

* P1 — model pisze `[1]`, a nie `[^1]`, więc `is_usable` odrzucał poprawną
  treść i 20% projektów po cichu schodziło do szablonu,
* P3 — model dokleja blok definicji przypisów, który trafiał do eksportu.

Ten plik zamyka lukę: przepuszcza **zarejestrowaną odpowiedź Mistrala** przez
pełną ścieżkę `LlmDrafting.draft()` — z prawdziwym `OpenAICompatibleLLM`,
a nie atrapą modelu. Sieci nie dotyka, więc działa w CI.

Test na żywo (`MISTRAL_LIVE=1`) sprawdza to samo na prawdziwym API. Domyślnie
pomijany, bo wymaga klucza i sieci.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from sqlalchemy import Engine, create_engine

from app.adapters.fakes.anonymize import FakeAnonymizer
from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.fakes.cases import FakeCaseRepository
from app.adapters.fakes.documents import FakeDocumentStore
from app.adapters.real.drafting import LlmDrafting
from app.adapters.real.inference import OpenAICompatibleLLM
from app.contracts import DraftRequest
from app.core.settings import Settings

CASE_ID = UUID("c0000001-0000-4000-8000-000000000001")

Handler = Callable[[httpx.Request], httpx.Response]

#: Klucz czytany przy imporcie modułu — fixture `_clean_env` czyści `LLM_*`
#: przed każdym testem, więc `os.getenv` w środku testu widziałby pustkę.
_LIVE_KEY = os.getenv("LLM_API_KEY", "")

#: Odpowiedź w dokładnie takim kształcie, jaki zwrócił `mistral-small-latest`
#: w pomiarach z raportu: odnośniki `[n]` zamiast `[^n]` i blok definicji
#: przypisów na końcu. To ten tekst przepadał w `is_usable`.
MISTRAL_CONTENT = """## Podstawa prawna

Zgodnie z art. 13 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do informacji
publicznej udostępnianie informacji publicznej na wniosek następuje bez zbędnej
zwłoki, nie później niż w terminie 14 dni od dnia złożenia wniosku [1]. Informacja
publiczna, która nie została udostępniona w Biuletynie Informacji Publicznej, jest
udostępniana na wniosek [2].

## Odpowiedź

W odpowiedzi na wniosek o udostępnienie informacji publicznej uprzejmie informuję,
co następuje. Wynagrodzenia pracowników samorządowych zatrudnionych na stanowiskach
kierowniczych stanowią informację publiczną [3].

## Pouczenie

Odmowa udostępnienia informacji publicznej następuje w drodze decyzji [4].

[^1]: art. 13 ust. 1 ustawy o dostępie do informacji publicznej
[^2]: art. 10 ust. 1 ustawy o dostępie do informacji publicznej
[^3]: art. 5 ust. 2 ustawy o dostępie do informacji publicznej
[^4]: art. 16 ustawy o dostępie do informacji publicznej
"""


def _chat_response(content: str) -> httpx.Response:
    """Odpowiedź `/chat/completions` w formacie OpenAI, jaką zwraca Mistral."""
    return httpx.Response(
        200,
        json={
            "id": "cmpl-test",
            "object": "chat.completion",
            "model": "mistral-small-latest",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 900, "completion_tokens": 420, "total_tokens": 1320},
        },
    )


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "llm_provider": "mistral",
        "llm_model": "mistral-small-latest",
        "llm_api_key": "test-key",
        "llm_timeout_s": 5.0,
        "offline": False,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Konfiguracja modeli pochodzi z argumentów testu, nie ze środowiska."""
    for name in ("OFFLINE", "LLM_PROVIDER", "LLM_MODEL", "LLM_BASE_URL", "LLM_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    db_engine = create_engine(f"sqlite:///{tmp_path / 'mistral.db'}", future=True)
    yield db_engine
    db_engine.dispose()


def _drafting(engine: Engine, handler: Handler) -> LlmDrafting:
    """Realny adapter generatora z realnym klientem modelu i atrapami portów."""
    return LlmDrafting(
        engine=engine,
        llm=OpenAICompatibleLLM(
            settings=_settings(), transport=httpx.MockTransport(handler)
        ),
        cases=FakeCaseRepository(),
        archive=FakeArchiveSearch(),
        documents=FakeDocumentStore(),
        anonymizer=FakeAnonymizer(),
    )


class TestRecordedMistralResponse:
    """Zarejestrowana odpowiedź Mistrala przechodzi przez całą ścieżkę."""

    def test_projekt_pochodzi_z_modelu_a_nie_z_szablonu(self, engine: Engine) -> None:
        """P1: przed poprawką ta odpowiedź lądowała w `unsupported` jako degradacja."""
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return _chat_response(MISTRAL_CONTENT)

        draft = _drafting(engine, handler).draft(DraftRequest(case_id=CASE_ID))

        assert draft.degraded is False
        assert draft.degraded_reason is None
        assert "Wynagrodzenia pracowników samorządowych" in draft.body

    def test_odnosniki_sa_w_formacie_przypisow(self, engine: Engine) -> None:
        """P1: `[n]` z odpowiedzi modelu zamienia się na `[^n]`."""
        draft = _drafting(engine, lambda _: _chat_response(MISTRAL_CONTENT)).draft(
            DraftRequest(case_id=CASE_ID)
        )

        assert "[^1]" in draft.body
        assert "[1]" not in draft.body

    def test_definicje_przypisow_nie_trafiaja_do_pisma(self, engine: Engine) -> None:
        """P3: blok `[^1]: …` nie jest treścią pisma."""
        draft = _drafting(engine, lambda _: _chat_response(MISTRAL_CONTENT)).draft(
            DraftRequest(case_id=CASE_ID)
        )

        assert "[^1]:" not in draft.body
        assert "[^4]:" not in draft.body
        assert not draft.body.rstrip().endswith("informacji publicznej")

    def test_cytowania_pokrywaja_tresc(self, engine: Engine) -> None:
        draft = _drafting(engine, lambda _: _chat_response(MISTRAL_CONTENT)).draft(
            DraftRequest(case_id=CASE_ID)
        )

        assert draft.citations
        assert all(citation.ref > 0 for citation in draft.citations)

    def test_zadanie_idzie_na_endpoint_mistrala(self, engine: Engine) -> None:
        """Kontrakt dostawcy: adres, model i nagłówek z kluczem."""
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return _chat_response(MISTRAL_CONTENT)

        _drafting(engine, handler).draft(DraftRequest(case_id=CASE_ID))

        assert len(seen) == 1
        request = seen[0]
        assert str(request.url) == "https://api.mistral.ai/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "mistral-small-latest"
        assert payload["stream"] is False
        assert payload["messages"][0]["role"] == "system"

    def test_prompt_zawiera_zadanie_i_zrodla(self, engine: Engine) -> None:
        seen: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request)
            return _chat_response(MISTRAL_CONTENT)

        _drafting(engine, handler).draft(DraftRequest(case_id=CASE_ID))

        prompt = json.loads(seen[0].content)["messages"][-1]["content"]
        assert "TWARDE WYMAGANIE" in prompt
        assert "ŹRÓDŁA" in prompt
        assert "BKS.IV.1431.1.2026" in prompt


@pytest.mark.skipif(
    os.getenv("MISTRAL_LIVE") != "1",
    reason="test na żywo — ustaw MISTRAL_LIVE=1 i LLM_API_KEY, żeby wołać prawdziwe API",
)
class TestLiveMistral:
    """Ten sam kontrakt na prawdziwym API. Domyślnie pomijany."""

    def test_zywy_model_daje_uzywalny_projekt(self, engine: Engine) -> None:
        if not _LIVE_KEY:
            pytest.skip("brak LLM_API_KEY")

        drafting = LlmDrafting(
            engine=engine,
            llm=OpenAICompatibleLLM(
                settings=_settings(llm_api_key=_LIVE_KEY, llm_timeout_s=60.0)
            ),
            cases=FakeCaseRepository(),
            archive=FakeArchiveSearch(),
            documents=FakeDocumentStore(),
            anonymizer=FakeAnonymizer(),
        )

        draft = drafting.draft(DraftRequest(case_id=CASE_ID))

        assert draft.degraded is False, (
            "model zwrócił treść, której nie dało się wykorzystać — "
            f"powód: {draft.degraded_reason}"
        )
        assert "[^1]:" not in draft.body
        assert draft.citations
