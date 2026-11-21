"""Fixtures testów generatora odpowiedzi (WS5)."""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Callable, Iterator
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import Engine, create_engine

from app.adapters.fakes.anonymize import FakeAnonymizer
from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.fakes.cases import FakeCaseRepository
from app.adapters.fakes.documents import FakeDocumentStore
from app.adapters.fakes.inference import FakeLLM
from app.adapters.real.drafting import LlmDrafting
from app.core import container

CASE_ID = UUID("c0000001-0000-4000-8000-000000000001")
OTHER_CASE_ID = UUID("c0000001-0000-4000-8000-000000000005")

MODEL_BODY = """## Podstawa prawna

Udostępnianie informacji publicznej na wniosek następuje w terminie 14 dni [^1].

## Odpowiedź

W odpowiedzi na wniosek o udostępnienie informacji publicznej uprzejmie informuję,
co następuje. Wynagrodzenia pracowników samorządowych stanowią informację publiczną
w zakresie osób zajmujących kierownicze stanowiska [^6].

## Pouczenie

Odmowa udostępnienia informacji publicznej następuje w drodze decyzji [^4].
"""


class StubLLM(FakeLLM):
    """Model sterowany w teście: zwraca zadany tekst albo zadany błąd."""

    def __init__(self, output: str = "", error: Exception | None = None) -> None:
        super().__init__()
        self._output = output
        self._error = error
        self.prompts: list[str] = []
        self.systems: list[str | None] = []

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> str:
        self.prompts.append(prompt)
        self.systems.append(system)
        if self._error is not None:
            raise self._error
        return self._output


def docx_text(blob: bytes) -> str:
    """Tekst z pliku DOCX — bez znaczników XML, do sprawdzeń w testach."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    return re.sub(r"<[^>]+>", "", xml)


def pdf_text(blob: bytes) -> str:
    """Tekst z pliku PDF — pdfplumber czyta warstwę tekstową."""
    import pdfplumber

    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


@pytest.fixture(autouse=True)
def _reset_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    """Osobna baza SQLite na test — nie dotykamy `data/app.db`."""
    db_engine = create_engine(f"sqlite:///{tmp_path / 'drafting.db'}", future=True)
    yield db_engine
    db_engine.dispose()


@pytest.fixture
def cases() -> FakeCaseRepository:
    return FakeCaseRepository()


@pytest.fixture
def archive() -> FakeArchiveSearch:
    return FakeArchiveSearch()


@pytest.fixture
def documents() -> FakeDocumentStore:
    return FakeDocumentStore()


@pytest.fixture
def anonymizer() -> FakeAnonymizer:
    return FakeAnonymizer()


@pytest.fixture
def drafting(
    engine: Engine,
    cases: FakeCaseRepository,
    archive: FakeArchiveSearch,
    documents: FakeDocumentStore,
    anonymizer: FakeAnonymizer,
) -> LlmDrafting:
    """Adapter realny z modelem atrapowym i atrapami pozostałych portów."""
    return LlmDrafting(
        engine=engine,
        llm=FakeLLM(),
        cases=cases,
        archive=archive,
        documents=documents,
        anonymizer=anonymizer,
    )


@pytest.fixture
def make_drafting(
    engine: Engine,
    cases: FakeCaseRepository,
    archive: FakeArchiveSearch,
    documents: FakeDocumentStore,
    anonymizer: FakeAnonymizer,
) -> Callable[[FakeLLM], LlmDrafting]:
    """Fabryka adaptera z podstawionym modelem — do testów degradacji."""

    def _make(llm: FakeLLM) -> LlmDrafting:
        return LlmDrafting(
            engine=engine,
            llm=llm,
            cases=cases,
            archive=archive,
            documents=documents,
            anonymizer=anonymizer,
        )

    return _make
