"""Testy podstawy prawnej z wgranych aktów w trybie demo (atrapa generatora).

Atrapa ma zaszyty szablon podstawy prawnej (art. 13 UDIP). Bez tych testów
wgrana ustawa działałaby tylko w trybie `real`, a demo — które chodzi na
atrapie — pokazywałoby urzędnikowi, że wgranie ustawy nic nie zmienia.
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest

from app.adapters.fakes.documents import FakeDocumentStore
from app.adapters.fakes.drafting import FakeDrafting
from app.contracts import DocumentKind, DraftRequest
from app.core import container

CASE_ID = UUID("c0000001-0000-4000-8000-000000000005")

USTAWA = (
    "Ustawa o ponownym wykorzystywaniu informacji sektora publicznego\n\n"
    "Art. 5. 1. Informacje sektora publicznego udostępniane są do ponownego "
    "wykorzystywania na wniosek.\n\n"
    "Art. 6. 1. Podmiot zobowiązany udostępnia informacje w formacie otwartym.\n"
)


@pytest.fixture(autouse=True)
def _clean_container() -> Iterator[None]:
    container.reset()
    yield
    container.reset()


@pytest.fixture
def documents() -> FakeDocumentStore:
    store = FakeDocumentStore()
    container._instances["ingest"] = store
    return store


def _wgraj(store: FakeDocumentStore, kind: DocumentKind, title: str) -> None:
    store.create(
        blob=USTAWA.encode("utf-8"),
        filename="ustawa.txt",
        kind=kind,
        title=title,
    )


def test_bez_wgranych_aktow_podstawa_jest_dotychczasowa() -> None:
    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID))

    assert len(draft.citations) == 1
    assert draft.citations[0].source_id == "udip"
    assert "Art. 5." not in draft.body


def test_wgrana_ustawa_wchodzi_do_podstawy_prawnej(documents: FakeDocumentStore) -> None:
    _wgraj(documents, DocumentKind.USTAWA, "Ustawa o ponownym wykorzystywaniu")

    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID))

    assert len(draft.citations) == 3
    assert draft.citations[0].source_id == "udip"
    labels = [citation.label for citation in draft.citations[1:]]
    assert any("art. 5" in label for label in labels)
    assert any("art. 6" in label for label in labels)
    assert "Art. 5." in draft.body
    assert "[^2]" in draft.body


def test_wgrane_zarzadzenie_tez_wchodzi(documents: FakeDocumentStore) -> None:
    _wgraj(documents, DocumentKind.ZARZADZENIE, "Zarządzenie w sprawie obiegu")

    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID))

    assert len(draft.citations) == 3
    assert any(
        "Zarządzenie w sprawie obiegu" in citation.label
        for citation in draft.citations
    )
    assert "Art. 5." in draft.body


def test_dokument_innego_rodzaju_nie_jest_podstawa_prawna(
    documents: FakeDocumentStore,
) -> None:
    _wgraj(documents, DocumentKind.INNE, "Notatka wewnętrzna")

    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID))

    assert len(draft.citations) == 1
    assert "Notatka wewnętrzna" not in draft.body


def test_wylaczenie_ustaw_usuwa_takze_wgrane(documents: FakeDocumentStore) -> None:
    _wgraj(documents, DocumentKind.USTAWA, "Ustawa o ponownym wykorzystywaniu")

    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID, use_statutes=False))

    assert draft.citations == []
    assert "Art. 5." not in draft.body


def test_brak_magazynu_dokumentow_nie_wywraca_projektu() -> None:
    """Gdy magazyn zawiedzie, atrapa zostaje przy samym szablonie."""

    class _Broken:
        def list(self, **_: object) -> list[object]:
            raise RuntimeError("baza padła")

    container._instances["ingest"] = _Broken()

    draft = FakeDrafting().draft(DraftRequest(case_id=CASE_ID))

    assert len(draft.citations) == 1
