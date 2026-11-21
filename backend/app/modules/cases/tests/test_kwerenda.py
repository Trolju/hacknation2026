"""Testy przedłużenia terminu w kwerendzie (W12: „kwerenda + liczba dni”).

Ten sam zestaw uruchamiamy na atrapie i na repozytorium SQL — oba adaptery
muszą przesuwać termin identycznie.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.contracts import CaseStatus, TransitionRequest
from app.core import container
from app.core.errors import ValidationFailed
from app.modules.cases.service import CaseService
from app.ports.cases import CaseRepositoryPort

#: Wniosek z fixtures w stanie `zapytania_wyslane` — jedyny krok do kwerendy.
CASE_ID = UUID("c0000001-0000-4000-8000-000000000001")


def _deadline(repo: CaseRepositoryPort) -> date:
    return repo.get(CASE_ID).deadline


def test_kwerenda_przesuwa_termin_o_podana_liczbę_dni(
    service: CaseService, repo: CaseRepositoryPort
) -> None:
    before = _deadline(repo)

    case = service.transition(
        CASE_ID, TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=14)
    )

    assert case.deadline == before + timedelta(days=14)
    assert case.kwerenda_days == 14


def test_kwerenda_bez_liczby_dni_nie_zmienia_terminu(
    service: CaseService, repo: CaseRepositoryPort
) -> None:
    before = _deadline(repo)

    case = service.transition(CASE_ID, TransitionRequest(to=CaseStatus.KWERENDA))

    assert case.deadline == before
    assert case.kwerenda_days is None


def test_kolejne_kwerendy_sumują_przedłużenie(
    service: CaseService, repo: CaseRepositoryPort
) -> None:
    before = _deadline(repo)

    service.transition(CASE_ID, TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=7))
    service.transition(
        CASE_ID,
        TransitionRequest(
            to=CaseStatus.ZAPYTANIA_WYSLANE, note="Wracam do zbierania odpowiedzi"
        ),
    )
    case = service.transition(
        CASE_ID, TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=5)
    )

    assert case.deadline == before + timedelta(days=12)
    assert case.kwerenda_days == 12


def test_przedłużenie_przy_innej_zmianie_stanu_jest_odrzucane(
    service: CaseService,
) -> None:
    with pytest.raises(ValidationFailed) as exc:
        service.transition(
            CASE_ID,
            TransitionRequest(to=CaseStatus.PRZYGOTOWANA_ODPOWIEDZ, kwerenda_days=7),
        )

    assert exc.value.details["field"] == "kwerenda_days"


def test_liczba_dni_poza_zakresem_jest_odrzucana() -> None:
    with pytest.raises(ValidationError):
        TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=0)
    with pytest.raises(ValidationError):
        TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=61)


def test_termin_w_kwerendzie_jest_widoczny_w_odczycie(
    service: CaseService, repo: CaseRepositoryPort
) -> None:
    service.transition(CASE_ID, TransitionRequest(to=CaseStatus.KWERENDA, kwerenda_days=10))

    detail = repo.get(CASE_ID)

    assert detail.kwerenda_days == 10
    assert detail.status is CaseStatus.KWERENDA


# ──────────────────────────────── ścieżka HTTP ──────────────────────────────
@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    container.reset()
    yield TestClient(app)
    container.reset()


def test_api_przesuwa_termin_i_zwraca_liczbe_dni(client: TestClient) -> None:
    before = client.get(f"/api/cases/{CASE_ID}").json()["deadline"]

    response = client.post(
        f"/api/cases/{CASE_ID}/transition",
        json={"to": "kwerenda", "kwerenda_days": 14},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["kwerenda_days"] == 14
    assert payload["deadline"] == (
        date.fromisoformat(before) + timedelta(days=14)
    ).isoformat()


def test_api_odrzuca_liczbe_dni_przy_innej_zmianie(client: TestClient) -> None:
    response = client.post(
        f"/api/cases/{CASE_ID}/transition",
        json={"to": "przygotowana_odpowiedz", "kwerenda_days": 7},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_failed"


def test_api_odrzuca_liczbe_dni_spoza_zakresu(client: TestClient) -> None:
    response = client.post(
        f"/api/cases/{CASE_ID}/transition",
        json={"to": "kwerenda", "kwerenda_days": 999},
    )

    assert response.status_code == 422
