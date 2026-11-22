"""Test end-to-end całej ścieżki urzędnika — wszystkie moduły w trybie `real`.

Jeden test przechodzi drogę od wgrania skanu wniosku do wpisu w dzienniku
audytu, wyłącznie przez HTTP (`TestClient`). Każdy krok odpowiada temu, co
w aplikacji robi urzędnik, i sprawdza wynik widoczny w interfejsie:

1. wgranie wniosku PDF → dokument `indexed`, tekst z polskimi znakami,
2. odczyt sprawy z kalendarza → `days_remaining` i `urgency`,
3. podobne sprawy z archiwum → niepuste, score malejąco,
4. sugestia komórek organizacyjnych → niepusta, pewność w 0..1,
5. zapytanie do komórek → treść z numerem sprawy i terminem,
6. projekt odpowiedzi → niepusty, z cytowaniami,
7. zapis projektu (`PATCH`) → nowa treść i kolejna wersja w historii,
8. eksport DOCX i PDF → nagłówki `PK` i `%PDF`,
9. anonimizacja treści projektu → nazwisko i PESEL z `fixtures/` znikają,
10. przejście stanu `nowy → zapytania_wyslane → przygotowana_odpowiedz →
    odpowiedz_wyslana` → statusy się zgadzają, `response_date` ustawione,
11. dziennik audytu → zawiera wpisy dla wykonanych operacji.

Test jest wolny od sieci i modeli: warstwa `inference` w trybie `real` nie
znajduje serwera modelu, więc generator odpowiedzi schodzi do szablonu —
dokładnie tak, jak w środowisku demonstracyjnym.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

import app.adapters.real.cases as real_cases
import app.modules.drafting.repository as draft_repository
from app.adapters.real.anonymize import NerAnonymizer
from app.adapters.real.archive import VectorArchiveSearch
from app.adapters.real.audit import SqlAuditLog
from app.adapters.real.cases import SqlCaseRepository
from app.adapters.real.documents import SqlDocumentStore
from app.adapters.real.drafting import LlmDrafting
from app.adapters.real.routing import KeywordDepartmentRouter
from app.core import container, db
from app.core.settings import settings
from app.main import app

# „Dziś” zakotwiczone jak w demo — dzięki temu dni do terminu są policzalne.
TODAY = date(2026, 3, 16)

MODULES = (
    "cases",
    "ingest",
    "archive",
    "routing",
    "drafting",
    "anonymize",
    "inference",
    "audit",
)

APPLICATION = "wniosek-01-wynagrodzenia.pdf"
CASE_NUMBER = "BKS.IV.1431.11.2026"
CASE_SUBJECT = "Wynagrodzenia pracowników Urzędu Miasta w 2025 r."
INFLOW_DATE = "2026-02-20"
DEADLINE = "2026-03-06"  # inflow_date + 14 dni z polityki terminów
DAYS_REMAINING = -10  # 16 marca 2026 minus termin 6 marca 2026


# ────────────────────────────── środowisko testu ──────────────────────────────
@pytest.fixture
def real_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    """Włącza wszystkie moduły w trybie `real` na tymczasowej bazie i uploadach."""
    for name in MODULES:
        monkeypatch.setenv(f"MODULE_MODE_{name.upper()}", "real")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "demo_today", TODAY)

    engine: Engine = create_engine(
        f"sqlite:///{tmp_path / 'e2e.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    # Adaptery realne biorą silnik z `app.core.db` (dokumenty, audyt, archiwum)
    # albo trzymają referencję z czasu importu (wnioski, projekty). Podmieniamy
    # wszystkie trzy miejsca, żeby test nie dotknął `backend/data/app.db`.
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(real_cases, "default_engine", engine)
    monkeypatch.setattr(draft_repository, "default_engine", engine)

    container.reset()
    try:
        yield TestClient(app)
    finally:
        container.reset()
        engine.dispose()


# ─────────────────────────────── funkcje pomocnicze ───────────────────────────
def _assert_real_adapters() -> None:
    """Sprawdza, że kontener naprawdę wydał adaptery realne, nie atrapy.

    `/api/health` raportuje konfigurację, a nie faktycznie wybraną klasę —
    brakujący adapter realny po cichu wraca do atrapy, więc pytamy kontener.
    """
    assert isinstance(container.get_cases(), SqlCaseRepository)
    assert isinstance(container.get_documents(), SqlDocumentStore)
    assert isinstance(container.get_archive(), VectorArchiveSearch)
    assert isinstance(container.get_routing(), KeywordDepartmentRouter)
    assert isinstance(container.get_drafting(), LlmDrafting)
    assert isinstance(container.get_anonymizer(), NerAnonymizer)
    assert isinstance(container.get_audit(), SqlAuditLog)


def _upload_application(client: TestClient) -> dict[str, Any]:
    """Krok 1: wgranie skanu wniosku (PDF) do bazy wiedzy."""
    path = settings.fixtures_dir / "documents" / APPLICATION
    with path.open("rb") as handle:
        response = client.post(
            "/api/documents",
            files={"file": (path.name, handle, "application/pdf")},
            data={"kind": "wniosek"},
        )
    assert response.status_code == 201, response.text
    return response.json()


def _register_case(client: TestClient, document_id: str) -> dict[str, Any]:
    """Rejestracja sprawy w kalendarzu, z wgranym skanem jako źródłem."""
    response = client.post(
        "/api/cases",
        json={
            "case_number": CASE_NUMBER,
            "subject": CASE_SUBJECT,
            "inflow_date": INFLOW_DATE,
            "handler_initials": "JK",
            "applicant_type": "media",
            "source_document_id": document_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _transition(client: TestClient, case_id: str, to: str) -> dict[str, Any]:
    """Przejście stanu sprawy — bez notatki, bo wszystkie idą naprzód."""
    response = client.post(f"/api/cases/{case_id}/transition", json={"to": to})
    assert response.status_code == 200, response.text
    return response.json()


def _applicant_line() -> dict[str, Any]:
    """Rekord z `fixtures/anonymization/labeled.jsonl` — nazwisko i numer PESEL.

    Projekt odpowiedzi cytuje wniosek, więc niesie nazwisko wnioskodawcy, ale
    numeru PESEL wniosek nie podaje. Doklejamy zdanie z fixtures, żeby sprawdzić
    oba rodzaje danych w jednym przebiegu anonimizatora.
    """
    path = settings.fixtures_dir / "anonymization" / "labeled.jsonl"
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


# ──────────────────────────────── test główny ─────────────────────────────────
def test_pelna_sciezka_urzednika_w_trybie_real(real_client: TestClient) -> None:
    """Cała droga wniosku: od skanu do wpisu w dzienniku audytu."""
    client = real_client

    # Wszystkie moduły muszą naprawdę działać na implementacjach realnych —
    # inaczej test sprawdzałby atrapy i nie wychwyciłby rozjazdu integracji.
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["modules"] == {name: "real" for name in MODULES}
    _assert_real_adapters()

    # ── Krok 1. Wgranie wniosku PDF ──────────────────────────────────────────
    # Skan trafia do bazy wiedzy: parser czyta tekst, dzieli go na fragmenty
    # z numerem strony i oznacza dokument jako `indexed`.
    document = _upload_application(client)
    assert document["status"] == "indexed"
    assert document["error"] is None
    assert document["chunk_count"] >= 1

    detail = client.get(f"/api/documents/{document['id']}").json()
    assert "WNIOSEK O UDOSTĘPNIENIE INFORMACJI PUBLICZNEJ" in detail["text"]
    assert "Gdańska" in detail["text"]  # polskie znaki przechodzą przez PDF
    assert "Wysokości wynagrodzeń" in detail["text"]

    chunks = client.get(f"/api/documents/{document['id']}/chunks").json()
    assert chunks
    # Kontrakt wymaga offsetu w każdym fragmencie — inaczej cytowanie nie działa.
    assert all(chunk["page"] is not None or chunk["section"] for chunk in chunks)

    # ── Krok 2. Odczyt sprawy z kalendarza ───────────────────────────────────
    # Sprawa powstaje z wgranym skanem jako źródłem; termin liczy polityka
    # 14 dni, a `days_remaining` i `urgency` wylicza `app.core.derive`.
    case = _register_case(client, document["id"])
    assert case["status"] == "nowy"
    assert case["deadline"] == DEADLINE
    assert case["source_document_id"] == document["id"]

    calendar = client.get("/api/cases").json()
    assert any(row["id"] == case["id"] for row in calendar)
    assert [row["deadline"] for row in calendar] == sorted(
        row["deadline"] for row in calendar
    )

    detail = client.get(f"/api/cases/{case['id']}").json()
    assert detail["days_remaining"] == DAYS_REMAINING
    assert detail["urgency"] == "overdue"
    assert detail["days_remaining"] == (
        date.fromisoformat(detail["deadline"]) - TODAY
    ).days

    # ── Krok 3. Podobne sprawy w archiwum ────────────────────────────────────
    similar = client.post(
        "/api/archive/similar",
        json={
            "text": "Wynagrodzenia pracowników Urzędu Miasta na stanowiskach kierowniczych",
            "k": 5,
        },
    ).json()
    assert similar
    scores = [row["score"] for row in similar]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)
    # Najbliższa sprawa archiwalna to zeszłoroczne wynagrodzenia.
    assert similar[0]["archive_id"] == "a0001"
    assert similar[0]["case_number"].startswith("BKS.IV.1431.")

    # ── Krok 4. Sugestia komórek organizacyjnych ─────────────────────────────
    suggestions = client.post(
        "/api/routing/suggest", json={"text": case["subject"], "k": 3}
    ).json()
    assert suggestions
    assert all(0.0 <= row["confidence"] <= 1.0 for row in suggestions)
    assert all(row["department_id"] and row["name"] for row in suggestions)
    # Wynagrodzenia to Wydział Organizacji i Kadr.
    assert suggestions[0]["department_id"] == "wok"

    # ── Krok 5. Zapytanie do wybranych komórek ───────────────────────────────
    department_ids = [row["department_id"] for row in suggestions[:2]]
    inquiry = client.post(
        "/api/routing/inquiry",
        json={"case_id": case["id"], "department_ids": department_ids},
    ).json()
    assert inquiry["addressees"]
    assert case["case_number"] in inquiry["body"]
    assert "6 marca 2026" in inquiry["body"]  # termin odpowiedzi po polsku
    assert inquiry["title"].endswith(case["case_number"])

    # ── Krok 6. Projekt odpowiedzi ───────────────────────────────────────────
    # Model językowy nie jest dostępny, więc projekt powstaje z szablonu —
    # mimo to każde twierdzenie ma odnośnik do źródła.
    draft = client.post("/api/drafting/draft", json={"case_id": case["id"]}).json()
    assert draft["body"].strip()
    assert draft["citations"]
    assert all(citation["ref"] >= 1 for citation in draft["citations"])
    assert {citation["source_type"] for citation in draft["citations"]} >= {
        "statute",
        "archive",
        "document",
    }
    assert draft["title"].endswith(case["case_number"])
    # Wniosek z akt sprawy jest cytowany razem z nazwiskiem wnioskodawcy.
    assert "Kowalski" in draft["body"]

    # ── Krok 7. Zapis projektu po korekcie urzędnika ─────────────────────────
    edited_body = (
        f"{draft['body']}\n\n"
        "Uzupełniono po konsultacji z Wydziałem Organizacji i Kadr."
    )
    patched = client.patch(
        f"/api/drafting/{draft['id']}", json={"body": edited_body}
    ).json()
    assert patched["body"] == edited_body
    assert patched["updated_at"] is not None
    assert client.get(f"/api/drafting/{case['id']}").json()["body"] == edited_body

    # Historia wersji nie jest wystawiona w API (kontrakt zamrożony), więc
    # sprawdzamy ją na adapterze realnym — tym samym, którego używa aplikacja.
    drafting = container.get_drafting()
    assert isinstance(drafting, LlmDrafting)
    versions = drafting.history(draft["id"])
    assert [version.action for version in versions] == ["generated", "edited"]
    assert versions[-1].body == edited_body

    # ── Krok 8. Eksport DOCX i PDF ───────────────────────────────────────────
    docx = client.get(f"/api/drafting/{draft['id']}/export", params={"fmt": "docx"})
    assert docx.status_code == 200
    assert docx.content[:2] == b"PK"  # DOCX to archiwum ZIP
    assert "wordprocessingml" in docx.headers["content-type"]

    pdf = client.get(f"/api/drafting/{draft['id']}/export", params={"fmt": "pdf"})
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    assert pdf.headers["content-type"] == "application/pdf"

    # ── Krok 9. Anonimizacja treści projektu ─────────────────────────────────
    applicant = _applicant_line()
    text = f"{patched['body']}\n\n{applicant['text']}"
    spans = client.post("/api/anonymize/detect", json={"text": text}).json()
    assert spans
    assert all(0.0 <= span["confidence"] <= 1.0 for span in spans)

    anonymized = client.post(
        "/api/anonymize/apply", json={"text": text, "spans": spans}
    ).json()
    assert anonymized["removed_count"] == len(spans)
    assert "Kowalski" not in anonymized["text"]
    assert "85041212345" not in anonymized["text"]  # PESEL z fixtures
    # Numery spraw nie mogą być brane za NIP/REGON — zostają w treści.
    assert "BKS.IV.1431." in anonymized["text"]

    # ── Krok 10. Przejście stanu sprawy ──────────────────────────────────────
    # `kwerenda` jest opcjonalna, więc idziemy prosto do przygotowanej odpowiedzi.
    for status in ("zapytania_wyslane", "przygotowana_odpowiedz", "odpowiedz_wyslana"):
        assert _transition(client, case["id"], status)["status"] == status

    final = client.get(f"/api/cases/{case['id']}").json()
    assert final["status"] == "odpowiedz_wyslana"
    assert final["response_date"] == TODAY.isoformat()
    assert final["urgency"] == "closed"

    history = client.get(f"/api/cases/{case['id']}/history").json()
    assert [entry["to_value"] for entry in history if entry["action"] == "status_change"] == [
        "zapytania_wyslane",
        "przygotowana_odpowiedz",
        "odpowiedz_wyslana",
    ]

    # ── Krok 11. Dziennik audytu ─────────────────────────────────────────────
    entries = client.get("/api/audit", params={"limit": 100}).json()
    actions = {entry["action"] for entry in entries}
    assert {
        "case.created",
        "document.uploaded",
        "draft.generated",
        "draft.saved",
        "draft.exported",
        "case.transitioned",
    } <= actions

    case_entries = client.get("/api/audit", params={"case_id": case["id"]}).json()
    case_actions = [entry["action"] for entry in case_entries]
    assert {"case.created", "draft.generated", "draft.saved"} <= set(case_actions)
    assert case_actions.count("case.transitioned") == 3
    assert all(entry["case_id"] == case["id"] for entry in case_entries)
    assert all(entry["at"] for entry in case_entries)


# ──────────────────────────────── test negatywny ──────────────────────────────
def test_cofniecie_stanu_bez_notatki_konczy_sie_409(real_client: TestClient) -> None:
    """Cofnięcie o krok bez notatki jest zabronione — kontrakt mówi o 409."""
    client = real_client
    document = _upload_application(client)
    case = _register_case(client, document["id"])
    _transition(client, case["id"], "zapytania_wyslane")

    response = client.post(f"/api/cases/{case['id']}/transition", json={"to": "nowy"})

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "invalid_transition"
    assert body["details"]["reason"] == "note_required"
    assert body["message"] == "Cofnięcie stanu wymaga notatki."
    # Stan sprawy nie zmienił się po odrzuconym żądaniu.
    assert client.get(f"/api/cases/{case['id']}").json()["status"] == "zapytania_wyslane"
