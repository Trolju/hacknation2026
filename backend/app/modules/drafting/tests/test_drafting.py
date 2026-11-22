"""Testy generatora odpowiedzi (WS5).

Sprawdzamy trzy rzeczy, które decydują o użyteczności modułu:

1. projekt powstaje zawsze — także bez modelu (degradacja do szablonu),
2. każde twierdzenie ma źródło, a brak źródła jest widoczny w `unsupported`,
3. eksport DOCX/PDF otwiera się poprawnie, a wersja zanonimizowana nie
   zawiera danych osobowych.
"""

from __future__ import annotations

import io
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.real.drafting import (
    MODEL_ERROR_NOTE,
    OFFLINE_NOTE,
    UNUSABLE_NOTE,
    LlmDrafting,
)
from app.contracts import DocumentKind, DraftPatch, DraftRequest
from app.core import container
from app.core.errors import NotFound, OfflineViolation
from app.main import app
from app.modules.drafting.prompt import find_unsupported
from app.modules.drafting.tests.conftest import (
    CASE_ID,
    MODEL_BODY,
    OTHER_CASE_ID,
    StubLLM,
    docx_text,
    pdf_text,
)

PERSONAL_BODY = (
    "## Odpowiedź\n\n"
    "Wniosek złożył Jan Kowalski, PESEL 85041212345, zamieszkały przy "
    "ul. Gdańskiej 42/7 [^1].\n"
)


# ──────────────────────────────── generowanie ──────────────────────────────
def test_generuje_projekt_z_modelem_atrapowym(drafting: LlmDrafting) -> None:
    """Atrapa modelu nie przygotowuje pisma — projekt powstaje z szablonu."""
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert draft.case_id == CASE_ID
    assert draft.title.startswith("Projekt odpowiedzi na wniosek BKS.IV.1431.1.2026")
    assert "## Podstawa prawna" in draft.body
    assert "## Pouczenie" in draft.body
    assert draft.citations
    assert draft.degraded is True
    assert draft.degraded_reason == UNUSABLE_NOTE
    assert draft.unsupported == []
    assert draft.updated_at is None


def test_uzywa_tresci_modelu(make_drafting) -> None:
    """Poprawna odpowiedź modelu trafia do projektu bez zmian."""
    llm = StubLLM(output=MODEL_BODY)
    drafting = make_drafting(llm)

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "Wynagrodzenia pracowników samorządowych" in draft.body
    assert draft.unsupported == []
    assert draft.degraded is False
    assert draft.degraded_reason is None
    assert [citation.ref for citation in draft.citations] == [1, 4, 6]
    assert llm.prompts and "TWARDE WYMAGANIE" in llm.prompts[0]
    assert llm.systems and "asystentem urzędnika" in (llm.systems[0] or "")


def test_prompt_zawiera_zrodla_i_sprawe(make_drafting) -> None:
    llm = StubLLM(output=MODEL_BODY)
    drafting = make_drafting(llm)

    drafting.draft(DraftRequest(case_id=CASE_ID))

    prompt = llm.prompts[0]
    assert "BKS.IV.1431.1.2026" in prompt
    assert "[1] (przepis) art. 13" in prompt
    assert "## Podstawa prawna" in prompt


def test_degraduje_przy_offline(make_drafting) -> None:
    """Tryb offline nie może zablokować pracy urzędnika."""
    drafting = make_drafting(StubLLM(error=OfflineViolation("Tryb offline.")))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "## Podstawa prawna" in draft.body
    assert draft.citations
    assert draft.degraded is True
    assert draft.degraded_reason == OFFLINE_NOTE
    assert draft.unsupported == []


def test_degraduje_przy_bledzie_modelu(make_drafting) -> None:
    drafting = make_drafting(StubLLM(error=RuntimeError("serwer modelu nie odpowiada")))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "## Odpowiedź" in draft.body
    assert draft.degraded is True
    assert draft.degraded_reason == MODEL_ERROR_NOTE
    assert draft.unsupported == []


def test_degraduje_przy_niepelnej_tresci_modelu(make_drafting) -> None:
    """Jedno zdanie od modelu to nie jest projekt pisma."""
    drafting = make_drafting(StubLLM(output="Nie mogę przygotować odpowiedzi."))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "## Podstawa prawna" in draft.body
    assert draft.degraded is True
    assert draft.degraded_reason == UNUSABLE_NOTE
    assert draft.unsupported == []


def test_bez_przepisow_i_archiwum(drafting: LlmDrafting) -> None:
    draft = drafting.draft(
        DraftRequest(case_id=CASE_ID, use_archive=False, use_statutes=False)
    )

    assert "Podstawa prawna zostanie uzupełniona." in draft.body
    assert draft.citations == []
    assert draft.degraded is True
    assert draft.degraded_reason == UNUSABLE_NOTE
    assert draft.unsupported == []


# ───────────────────────────────── cytowania ───────────────────────────────
def test_cytowania_maja_pelne_pola(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    refs = [citation.ref for citation in draft.citations]
    assert refs == sorted(set(refs))
    assert {citation.source_type for citation in draft.citations} == {
        "statute",
        "archive",
    }
    for citation in draft.citations:
        assert citation.source_id
        assert citation.label
        assert citation.excerpt

    statute = next(c for c in draft.citations if c.source_type == "statute")
    assert "art. 13" in statute.label
    assert "14 dni" in statute.excerpt


def test_cytowania_tylko_dla_uzytych_zrodel(make_drafting) -> None:
    drafting = make_drafting(StubLLM(output=MODEL_BODY))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert [citation.ref for citation in draft.citations] == [1, 4, 6]
    assert all(f"[^{citation.ref}]" in draft.body for citation in draft.citations)


# ─────────────────────────── twierdzenia bez źródła ────────────────────────
def test_twierdzenie_bez_zrodla_trafia_do_unsupported(make_drafting) -> None:
    body = MODEL_BODY + (
        "\nW 2025 roku wydano 120 decyzji o warunkach zabudowy.\n"
    )
    drafting = make_drafting(StubLLM(output=body))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "W 2025 roku wydano 120 decyzji o warunkach zabudowy." in draft.unsupported
    assert "W 2025 roku wydano 120 decyzji o warunkach zabudowy." in draft.body


def test_odnosnik_do_nieistniejacego_zrodla_jest_usuwany(make_drafting) -> None:
    body = MODEL_BODY + "\nOrgan działa na podstawie przepisów prawa [^99].\n"
    drafting = make_drafting(StubLLM(output=body))

    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert "[^99]" not in draft.body
    assert "Organ działa na podstawie przepisów prawa." in draft.unsupported


def test_zdania_formalne_nie_sa_oskarzane() -> None:
    body = (
        "## Odpowiedź\n\n"
        "W odpowiedzi na wniosek o udostępnienie informacji publicznej uprzejmie "
        "informuję, co następuje.\n\n"
        "Z upoważnienia Prezydenta Miasta Bydgoszczy\n"
    )

    assert find_unsupported(body, {1}) == []


# ──────────────────────────────── zapis wersji ─────────────────────────────
def test_zapis_i_odczyt_wersji(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    first = drafting.update(draft.id, DraftPatch(body="Pierwsza korekta urzędnika."))
    second = drafting.update(draft.id, DraftPatch(body="Druga korekta urzędnika."))

    assert first.id == second.id == draft.id
    assert second.body == "Druga korekta urzędnika."
    assert second.updated_at is not None
    assert drafting.get(CASE_ID).body == "Druga korekta urzędnika."

    versions = drafting.history(draft.id)
    assert [version.version for version in versions] == [1, 2, 3]
    assert [version.action for version in versions] == ["generated", "edited", "edited"]
    assert versions[1].body == "Pierwsza korekta urzędnika."
    assert versions[2].body == "Druga korekta urzędnika."
    assert all(version.actor == "urzędnik" for version in versions)
    assert versions[2].note and "znaków" in versions[2].note


def test_projekt_przezywa_nowa_instancje(
    engine, cases, archive, documents, anonymizer
) -> None:
    """Zapis w SQLite — po restarcie aplikacji projekt nadal jest dostępny."""
    first = LlmDrafting(
        engine=engine,
        llm=StubLLM(output=MODEL_BODY),
        cases=cases,
        archive=archive,
        documents=documents,
        anonymizer=anonymizer,
    )
    draft = first.draft(DraftRequest(case_id=CASE_ID))
    first.update(draft.id, DraftPatch(body="Treść po korekcie."))

    second = LlmDrafting(
        engine=engine,
        llm=StubLLM(output=MODEL_BODY),
        cases=cases,
        archive=archive,
        documents=documents,
        anonymizer=anonymizer,
    )

    restored = second.get(CASE_ID)
    assert restored.id == draft.id
    assert restored.body == "Treść po korekcie."
    assert restored.citations == draft.citations


def test_ponowne_generowanie_zachowuje_historie(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body="Korekta przed ponownym generowaniem."))

    regenerated = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert regenerated.id == draft.id
    assert regenerated.body != "Korekta przed ponownym generowaniem."
    assert [version.version for version in drafting.history(draft.id)] == [1, 2, 3]


def test_brak_projektu_dla_sprawy(drafting: LlmDrafting) -> None:
    with pytest.raises(NotFound):
        drafting.get(OTHER_CASE_ID)


def test_aktualizacja_nieistniejacego_projektu(drafting: LlmDrafting) -> None:
    with pytest.raises(NotFound):
        drafting.update(uuid4(), DraftPatch(body="Treść"))


# ────────────────────────────────── eksport ────────────────────────────────
def test_eksport_docx(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    blob, filename = drafting.export(draft.id, fmt="docx", anonymized=False)

    assert blob[:2] == b"PK"
    assert filename.endswith(".docx")
    text = docx_text(blob)
    assert "Projekt odpowiedzi na wniosek BKS.IV.1431.1.2026" in text
    assert "Podstawa prawna" in text
    assert "URZĄD MIASTA BYDGOSZCZY" in text
    assert "Biuro Komunikacji Społecznej" in text
    assert "BKS.IV.1431.1.2026" in text
    assert "Cytowania" in text
    assert "art. 13 ust. 1 i 2 ustawy o dostępie do informacji publicznej" in text

    # Plik musi dać się otworzyć czytnikiem DOCX, nie tylko rozpakować.
    import docx

    document = docx.Document(io.BytesIO(blob))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    assert any("Podstawa prawna" in paragraph for paragraph in paragraphs)
    assert any("Cytowania" in paragraph for paragraph in paragraphs)


def test_eksport_pdf(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    blob, filename = drafting.export(draft.id, fmt="pdf", anonymized=False)

    assert blob[:4] == b"%PDF"
    assert filename.endswith(".pdf")
    text = pdf_text(blob)
    assert "Podstawa prawna" in text
    assert "Cytowania" in text


def test_eksport_markdown(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    blob, filename = drafting.export(draft.id, fmt="md", anonymized=False)

    assert filename.endswith(".md")
    assert "## Cytowania" in blob.decode("utf-8")


def test_eksport_markdown_bez_caretow(drafting: LlmDrafting) -> None:
    """P16 — Markdown podaje odnośniki jak DOCX i PDF: `[n]`, nie `[^n]`."""
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(
        draft.id, DraftPatch(body="## Odpowiedź\n\nZdanie z odnośnikiem [^1].")
    )

    blob, _ = drafting.export(draft.id, fmt="md", anonymized=False)
    text = blob.decode("utf-8")

    assert "[^" not in text
    assert "Zdanie z odnośnikiem [1]." in text


def test_nazwa_pliku_eksportu_to_numer_sprawy(drafting: LlmDrafting) -> None:
    """P12 — urzędnik zapisuje plik z numerem sprawy, nie fragmentem UUID."""
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    _, filename = drafting.export(draft.id, fmt="docx", anonymized=False)

    assert filename == "odpowiedz-BKS.IV.1431.1.2026-projekt.docx"


def test_nazwa_pliku_anonimizowanego_tez_ma_numer_sprawy(
    drafting: LlmDrafting,
) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    _, filename = drafting.export(draft.id, fmt="pdf", anonymized=True)

    assert filename == "odpowiedz-BKS.IV.1431.1.2026-anon.pdf"


def test_eksport_anonimizowany_ukrywa_dane(drafting: LlmDrafting) -> None:
    """Dane osobowe pochodzą z `fixtures/anonymization/labeled.jsonl`."""
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    plain, _ = drafting.export(draft.id, fmt="docx", anonymized=False)
    hidden, filename = drafting.export(draft.id, fmt="docx", anonymized=True)

    assert "Kowalski" in docx_text(plain)
    assert "85041212345" in docx_text(plain)

    anonymized_text = docx_text(hidden)
    assert "Kowalski" not in anonymized_text
    assert "85041212345" not in anonymized_text
    assert "USUNIĘTO" in anonymized_text
    assert filename.endswith("-anon.docx")


def test_eksport_anonimizowany_ukrywa_dane_w_cytowaniach(
    drafting: LlmDrafting, documents
) -> None:
    """Lista cytowań też przechodzi przez anonimizator — nie tylko treść pisma."""
    document = documents.create(
        blob=(
            "Odpowiedź Wydziału Organizacji i Kadr. Sprawę prowadzi Jan Kowalski, "
            "tel. +48 601 234 567."
        ).encode(),
        filename="odpowiedz-wydzialu.txt",
        kind=DocumentKind.ODPOWIEDZ_WYDZIALU,
        case_id=CASE_ID,
    )

    draft = drafting.draft(
        DraftRequest(case_id=CASE_ID, department_reply_ids=[document.id])
    )
    assert any("Kowalski" in citation.excerpt for citation in draft.citations)

    plain, _ = drafting.export(draft.id, fmt="docx", anonymized=False)
    hidden, _ = drafting.export(draft.id, fmt="docx", anonymized=True)

    assert "Kowalski" in docx_text(plain)
    assert "Kowalski" not in docx_text(hidden)
    assert "601 234 567" not in docx_text(hidden)


def test_eksport_anonimizowany_pdf(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    blob, _ = drafting.export(draft.id, fmt="pdf", anonymized=True)

    assert blob[:4] == b"%PDF"
    assert "Kowalski" not in pdf_text(blob)


def test_eksport_nieznanego_formatu(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    with pytest.raises(NotFound):
        drafting.export(draft.id, fmt="odt", anonymized=False)


# ──────────────────────────────── integracja ───────────────────────────────
def test_kontener_zwraca_adapter_realny(monkeypatch, engine) -> None:
    monkeypatch.setattr("app.modules.drafting.repository.default_engine", engine)
    monkeypatch.setenv("MODULE_MODE_DRAFTING", "real")

    drafting = container.get_drafting()

    assert isinstance(drafting, LlmDrafting)


def test_api_deleguje_do_adaptera(drafting: LlmDrafting) -> None:
    app.dependency_overrides[container.get_drafting] = lambda: drafting
    try:
        client = TestClient(app)
        created = client.post("/api/drafting/draft", json={"case_id": str(CASE_ID)})
        assert created.status_code == 200
        draft = created.json()
        assert draft["citations"]

        fetched = client.get(f"/api/drafting/{CASE_ID}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == draft["id"]

        patched = client.patch(
            f"/api/drafting/{draft['id']}", json={"body": "Treść po korekcie."}
        )
        assert patched.status_code == 200
        assert patched.json()["body"] == "Treść po korekcie."

        exported = client.get(
            f"/api/drafting/{draft['id']}/export", params={"fmt": "docx"}
        )
        assert exported.status_code == 200
        assert exported.content[:2] == b"PK"
    finally:
        app.dependency_overrides.clear()


def test_api_zwraca_404_dla_braku_projektu(drafting: LlmDrafting) -> None:
    app.dependency_overrides[container.get_drafting] = lambda: drafting
    try:
        client = TestClient(app)
        response = client.get(f"/api/drafting/{OTHER_CASE_ID}")
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"
    finally:
        app.dependency_overrides.clear()


def test_nieznana_sprawa_konczy_sie_404(drafting: LlmDrafting) -> None:
    with pytest.raises(NotFound):
        drafting.draft(DraftRequest(case_id=UUID("00000000-0000-4000-8000-000000000000")))
