"""Testy licznika anonimizacji przy eksporcie.

Eksport anonimizowany musi powiedzieć, ile fragmentów faktycznie usunął.
Bez tego urzędnik dostaje plik identyczny z oryginałem i nie wie, czy
anonimizacja zadziałała, czy po prostu nie miała czego ukryć.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.fakes.drafting import FakeDrafting
from app.adapters.real.drafting import LlmDrafting
from app.contracts import DraftPatch, DraftRequest
from app.core import container
from app.core.errors import NotFound
from app.main import app
from app.modules.drafting.tests.conftest import CASE_ID, docx_text

PERSONAL_BODY = (
    "## Odpowiedź\n\n"
    "Wniosek złożył Jan Kowalski, PESEL 85041212345, zamieszkały przy "
    "ul. Gdańskiej 42/7 [^1].\n"
)


# ──────────────────────────────── adapter realny ───────────────────────────
def test_redactions_zero_gdy_brak_danych_osobowych(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    assert drafting.redactions(draft.id) == 0


def test_redactions_liczy_trafienia_w_tresci(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    # Imię i nazwisko, PESEL i adres — trzy niezależne trafienia.
    assert drafting.redactions(draft.id) >= 3


def test_redactions_nieistniejacy_projekt(drafting: LlmDrafting) -> None:
    with pytest.raises(NotFound):
        drafting.redactions(uuid4())


def test_redactions_zgodne_z_eksportem(drafting: LlmDrafting) -> None:
    """Licznik mówi prawdę: trafienia widać też w wyeksportowanym pliku."""
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    count = drafting.redactions(draft.id)
    plain, _ = drafting.export(draft.id, fmt="docx", anonymized=False)
    hidden, _ = drafting.export(draft.id, fmt="docx", anonymized=True)

    assert count > 0
    assert "Kowalski" in docx_text(plain)
    assert "Kowalski" not in docx_text(hidden)


# ──────────────────────────────── atrapa ───────────────────────────────────
def test_atrapa_tez_anonimizuje_tresc() -> None:
    """Atrapa nie może tylko zmieniać nazwy pliku — treść też musi zniknąć."""
    fake = FakeDrafting()
    draft = fake.draft(DraftRequest(case_id=CASE_ID))
    fake.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    plain, _ = fake.export(draft.id, fmt="docx", anonymized=False)
    hidden, _ = fake.export(draft.id, fmt="docx", anonymized=True)

    assert "Kowalski" in docx_text(plain)
    assert "Kowalski" not in docx_text(hidden)
    assert fake.redactions(draft.id) > 0


# ──────────────────────────────── router ───────────────────────────────────
def test_router_zwraca_naglowek_x_redactions(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))
    drafting.update(draft.id, DraftPatch(body=PERSONAL_BODY))

    app.dependency_overrides[container.get_drafting] = lambda: drafting
    try:
        client = TestClient(app)
        response = client.get(
            f"/api/drafting/{draft.id}/export",
            params={"fmt": "docx", "anonymized": "true"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert int(response.headers["X-Redactions"]) > 0


def test_router_zero_gdy_nie_anonimizujemy(drafting: LlmDrafting) -> None:
    draft = drafting.draft(DraftRequest(case_id=CASE_ID))

    app.dependency_overrides[container.get_drafting] = lambda: drafting
    try:
        client = TestClient(app)
        response = client.get(f"/api/drafting/{draft.id}/export", params={"fmt": "docx"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["X-Redactions"] == "0"
