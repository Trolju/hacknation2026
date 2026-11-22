"""Testy podstawy prawnej z wgranych ustaw i zarządzeń (W8).

Sprawdzamy cztery rzeczy, które decydują o tym, czy urzędnik może uczyć
system nowych aktów prawnych bez zmiany kodu:

1. wgrana ustawa i wgrane zarządzenie trafiają do podstawy prawnej projektu,
2. wgrany akt o tytule pliku z fixtures przykrywa ten plik — tak działa
   aktualizacja ustawy,
3. dokument o rodzaju „inne” nie jest podstawą prawną,
4. brak wgranych aktów nie zmienia dotychczasowego wyniku.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import UUID

from sqlalchemy import Engine

from app.adapters.fakes.documents import FakeDocumentStore
from app.adapters.real.documents import SqlDocumentStore
from app.adapters.real.drafting import LlmDrafting
from app.contracts import DocumentKind, DraftRequest
from app.modules.drafting.sources import (
    MAX_STATUTE_ARTICLES,
    Source,
    statute_sources,
)
from app.modules.drafting.template import MAX_UPLOADED_QUOTES
from app.modules.drafting.tests.conftest import CASE_ID, MODEL_BODY, StubLLM

USTAWA_TEKST = (
    "USTAWA o dostępie do informacji publicznej\n\n"
    "Art. 13. 1. Udostępnianie informacji publicznej na wniosek następuje bez "
    "zbędnej zwłoki, nie później jednak niż w terminie 14 dni od dnia złożenia "
    "wniosku.\n\n"
    "Art. 16. 1. Odmowa udostępnienia informacji publicznej następuje w drodze "
    "decyzji.\n"
)

# Ten sam akt po nowelizacji — po tekście poznajemy, która wersja wygrała.
USTAWA_PO_NOWELIZACJI = (
    "USTAWA o dostępie do informacji publicznej\n\n"
    "Art. 13. 1. Udostępnianie informacji publicznej na wniosek następuje bez "
    "zbędnej zwłoki, nie później jednak niż w terminie 21 dni od dnia złożenia "
    "wniosku.\n"
)

ZARZADZENIE_TEKST = (
    "ZARZĄDZENIE Nr 500/2026\nPREZYDENTA MIASTA BYDGOSZCZY\n\n"
    "§ 2. Wnioski o udostępnienie informacji publicznej rejestruje się w "
    "centralnym rejestrze wniosków UDIP.\n"
)

TYTUL_USTAWY = "Ustawa o dostępie do informacji publicznej"


def _wgrane(sources: Sequence[Source], document_id: UUID) -> list[Source]:
    """Źródła pochodzące z jednego wgranego dokumentu."""
    return [source for source in sources if source.source_id.startswith(f"{document_id}#")]


# ─────────────────────────── wgrany akt w podstawie ────────────────────────
def test_wgrana_ustawa_trafia_do_podstawy_prawnej(
    documents: FakeDocumentStore,
) -> None:
    document = documents.create(
        blob=USTAWA_TEKST.encode(),
        filename="ustawa-udip.txt",
        kind=DocumentKind.USTAWA,
        title=TYTUL_USTAWY,
    )

    sources = statute_sources(documents)
    wgrane = _wgrane(sources, document.id)

    assert [source.source_id for source in wgrane] == [
        f"{document.id}#Art. 13.",
        f"{document.id}#Art. 16.",
    ]
    assert all(source.source_type == "statute" for source in wgrane)
    assert wgrane[0].label == f"art. 13 — {TYTUL_USTAWY}"
    assert "14 dni" in wgrane[0].excerpt
    assert wgrane[0].text.startswith("Art. 13.")


def test_wgrane_zarzadzenie_trafia_do_podstawy_prawnej(
    documents: FakeDocumentStore,
) -> None:
    document = documents.create(
        blob=ZARZADZENIE_TEKST.encode(),
        filename="zarzadzenie-500-2026.txt",
        kind=DocumentKind.ZARZADZENIE,
        title="Zarządzenie nr 500/2026",
    )

    wgrane = _wgrane(statute_sources(documents), document.id)

    assert [source.source_id for source in wgrane] == [f"{document.id}#§ 2."]
    assert wgrane[0].source_type == "statute"
    assert wgrane[0].label == "§ 2 — Zarządzenie nr 500/2026"


def test_wgrana_ustawa_jest_cytowana_w_projekcie(
    drafting: LlmDrafting, documents: FakeDocumentStore
) -> None:
    """Projekt z szablonu też ma w podstawie prawnej wgrany akt."""
    document = documents.create(
        blob=USTAWA_TEKST.encode(),
        filename="ustawa-udip.txt",
        kind=DocumentKind.USTAWA,
        title=TYTUL_USTAWY,
    )

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    cytat = next(
        citation
        for citation in draft.citations
        if citation.source_id.startswith(f"{document.id}#")
    )
    assert cytat.source_type == "statute"
    assert cytat.label == f"art. 13 — {TYTUL_USTAWY}"
    assert "14 dni" in cytat.excerpt

    podstawa = draft.body.split("## Odpowiedź")[0]
    assert f"[^{cytat.ref}]" in podstawa
    assert TYTUL_USTAWY in podstawa


def test_prompt_oznacza_wgrana_ustawe_jako_przepis(
    make_drafting, documents: FakeDocumentStore
) -> None:
    documents.create(
        blob=USTAWA_TEKST.encode(),
        filename="ustawa-udip.txt",
        kind=DocumentKind.USTAWA,
        title=TYTUL_USTAWY,
    )
    llm = StubLLM(output=MODEL_BODY)

    make_drafting(llm).draft(DraftRequest(case_id=CASE_ID))

    assert f"(przepis) art. 13 — {TYTUL_USTAWY}" in llm.prompts[0]


def test_realny_magazyn_dokumentow_tez_daje_podstawe_prawna(
    engine: Engine, tmp_path: Path
) -> None:
    """Ścieżka produkcyjna: `SqlDocumentStore`, nie tylko atrapa w pamięci."""
    store = SqlDocumentStore(engine=engine, upload_dir=tmp_path / "uploads")
    document = store.create(
        blob=USTAWA_TEKST.encode(),
        filename="ustawa-udip.txt",
        kind=DocumentKind.USTAWA,
        title=TYTUL_USTAWY,
    )

    wgrane = _wgrane(statute_sources(store), document.id)

    assert [source.source_id for source in wgrane] == [
        f"{document.id}#Art. 13.",
        f"{document.id}#Art. 16.",
    ]
    assert wgrane[0].label == f"art. 13 — {TYTUL_USTAWY}"


# ──────────────────────────── aktualizacja ustawy ──────────────────────────
def test_wgrana_ustawa_przykrywa_fixtures_o_tym_samym_tytule(
    documents: FakeDocumentStore,
) -> None:
    documents.create(
        blob=USTAWA_PO_NOWELIZACJI.encode(),
        filename="tekst-jednolity-2026.txt",
        kind=DocumentKind.USTAWA,
        title="udip",
    )

    sources = statute_sources(documents)

    assert not any(source.source_id.startswith("udip#") for source in sources)
    assert any("21 dni" in source.text for source in sources)
    assert not any("14 dni" in source.text for source in sources)


def test_wgrana_ustawa_przykrywa_fixtures_po_nazwie_pliku(
    documents: FakeDocumentStore,
) -> None:
    """Tytuł dokumentu bywa dowolny — liczy się też nazwa wgranego pliku."""
    documents.create(
        blob=USTAWA_PO_NOWELIZACJI.encode(),
        filename="udip.txt",
        kind=DocumentKind.USTAWA,
        title="Tekst jednolity z 2026 r.",
    )

    sources = statute_sources(documents)

    assert not any(source.source_id.startswith("udip#") for source in sources)
    assert any("21 dni" in source.text for source in sources)


def test_wgrana_ustawa_przykrywa_fixtures_po_naglowku(
    documents: FakeDocumentStore,
) -> None:
    """Nagłówek aktu z pierwszej linii pliku też jest tytułem."""
    documents.create(
        blob=USTAWA_PO_NOWELIZACJI.encode(),
        filename="tekst-jednolity-2026.txt",
        kind=DocumentKind.USTAWA,
        title="USTAWA z dnia 6 września 2001 r. o dostępie do informacji publicznej",
    )

    sources = statute_sources(documents)

    assert not any(source.source_id.startswith("udip#") for source in sources)
    assert any("21 dni" in source.text for source in sources)


def test_aktualizacja_nie_rusza_pozostalych_fixtures(
    documents: FakeDocumentStore,
) -> None:
    documents.create(
        blob=USTAWA_PO_NOWELIZACJI.encode(),
        filename="udip.txt",
        kind=DocumentKind.USTAWA,
    )

    sources = statute_sources(documents)

    assert any(
        source.source_id == "zarzadzenie-412-2023#§ 4." for source in sources
    )


# ──────────────────────────── rodzaje nie-prawne ───────────────────────────
def test_dokument_inne_nie_trafia_do_podstawy_prawnej(
    documents: FakeDocumentStore,
) -> None:
    document = documents.create(
        blob=USTAWA_TEKST.encode(),
        filename="notatka.txt",
        kind=DocumentKind.INNE,
        title="Notatka z narady",
    )

    sources = statute_sources(documents)

    assert _wgrane(sources, document.id) == []
    assert sources == statute_sources()


def test_wniosek_i_odpowiedz_komorki_nie_trafiaja_do_podstawy_prawnej(
    documents: FakeDocumentStore,
) -> None:
    for kind, filename in (
        (DocumentKind.WNIOSEK, "wniosek.txt"),
        (DocumentKind.ODPOWIEDZ_WYDZIALU, "odpowiedz.txt"),
        (DocumentKind.ARCHIWUM, "archiwum.txt"),
    ):
        documents.create(
            blob=USTAWA_TEKST.encode(),
            filename=filename,
            kind=kind,
            title=TYTUL_USTAWY,
        )

    assert statute_sources(documents) == statute_sources()


# ───────────────────────────── brak wgranych aktów ─────────────────────────
def test_brak_wgranych_ustaw_nie_zmienia_wyniku(
    documents: FakeDocumentStore,
) -> None:
    assert statute_sources(documents) == statute_sources()
    assert [source.source_id for source in statute_sources()] == [
        "udip#Art. 13.",
        "udip#Art. 10.",
        "udip#Art. 5.",
        "udip#Art. 16.",
        "zarzadzenie-412-2023#§ 4.",
    ]


def test_wgrana_ustawa_bez_artykulow_nie_psuje_podstawy(
    documents: FakeDocumentStore,
) -> None:
    documents.create(
        blob=b"Notatka bez podzialu na artykuly i paragrafy.",
        filename="notatka.txt",
        kind=DocumentKind.USTAWA,
    )

    assert statute_sources(documents) == statute_sources()


def test_liczba_artykulow_wgranego_aktu_jest_ograniczona(
    documents: FakeDocumentStore,
) -> None:
    tekst = "USTAWA testowa\n\n" + "\n\n".join(
        f"Art. {numer}. Treść artykułu numer {numer}." for numer in range(1, 21)
    )
    document = documents.create(
        blob=tekst.encode(),
        filename="duza-ustawa.txt",
        kind=DocumentKind.USTAWA,
    )

    wgrane = _wgrane(statute_sources(documents), document.id)

    assert len(wgrane) == MAX_STATUTE_ARTICLES
    assert wgrane[0].source_id == f"{document.id}#Art. 1."


# ──────────────────────────── akta sprawy bez dubli ────────────────────────
def test_wgrana_ustawa_nie_duplikuje_sie_w_aktach_sprawy(
    drafting: LlmDrafting, documents: FakeDocumentStore
) -> None:
    """Ustawa podpięta do sprawy jest podstawą prawną, nie dokumentem sprawy."""
    document = documents.create(
        blob=USTAWA_TEKST.encode(),
        filename="ustawa-udip.txt",
        kind=DocumentKind.USTAWA,
        case_id=CASE_ID,
        title=TYTUL_USTAWY,
    )

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    identyfikatory = [citation.source_id for citation in draft.citations]
    assert str(document.id) not in identyfikatory
    assert any(
        identyfikator.startswith(f"{document.id}#") for identyfikator in identyfikatory
    )


# ────────────────── P2: cały akt to nie jest podstawa prawna ───────────────
#: Akt z dwunastoma artykułami, z których tylko dwa dotyczą wynagrodzeń —
#: czyli przedmiotu sprawy `CASE_ID`. Reszta to wypełniacz o organizacji.
DUZA_USTAWA = (
    "USTAWA o organizacji urzędu\n\n"
    + "\n\n".join(
        f"Art. {numer}. Przepis ustrojowy numer {numer} o wewnętrznej organizacji "
        "urzędu, bez związku z przedmiotem wniosku."
        for numer in range(1, 11)
    )
    + "\n\nArt. 11. Wynagrodzenia pracowników urzędu ustala się w regulaminie "
    "wynagradzania obowiązującym w urzędzie.\n\n"
    "Art. 12. Wynagrodzenia pracowników samorządowych są jawne w zakresie osób "
    "zajmujących kierownicze stanowiska.\n"
)


def test_caly_akt_nie_zalewa_podstawy_prawnej(
    drafting: LlmDrafting, documents: FakeDocumentStore
) -> None:
    """P2: dwanaście artykułów dawało dwanaście zdań w podstawie prawnej."""
    documents.create(
        blob=DUZA_USTAWA.encode(),
        filename="ustawa-organizacja.txt",
        kind=DocumentKind.USTAWA,
        title="Ustawa o organizacji urzędu",
    )

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    podstawa = draft.body.split("## Odpowiedź")[0]

    assert podstawa.count("Podstawę prawną stanowi") <= MAX_UPLOADED_QUOTES


def test_do_podstawy_trafiaja_przepisy_trafne_w_przedmiot(
    drafting: LlmDrafting, documents: FakeDocumentStore
) -> None:
    """Z całego aktu wybieramy artykuły o wynagrodzeniach, nie pierwsze z brzegu."""
    documents.create(
        blob=DUZA_USTAWA.encode(),
        filename="ustawa-organizacja.txt",
        kind=DocumentKind.USTAWA,
        title="Ustawa o organizacji urzędu",
    )

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    podstawa = draft.body.split("## Odpowiedź")[0]

    assert "Wynagrodzenia pracowników" in podstawa
    assert "Przepis ustrojowy numer 1" not in podstawa


def test_akt_bez_trafnego_przepisu_jest_wymieniony_bez_cytatu(
    drafting: LlmDrafting, documents: FakeDocumentStore
) -> None:
    """Gdy żaden przepis nie dotyczy wniosku, wymieniamy sam akt — bez cytatu."""
    documents.create(
        blob=(
            "USTAWA o organizacji urzędu\n\n"
            "Art. 1. Przepis ustrojowy o wewnętrznej organizacji urzędu.\n\n"
            "Art. 2. Kolejny przepis ustrojowy o organizacji urzędu.\n"
        ).encode(),
        filename="ustawa-organizacja.txt",
        kind=DocumentKind.USTAWA,
        title="Ustawa o organizacji urzędu",
    )

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    podstawa = draft.body.split("## Odpowiedź")[0]

    assert "Podstawę prawną stanowi dodatkowo Ustawa o organizacji urzędu" in podstawa
    assert "Przepis ustrojowy" not in podstawa
