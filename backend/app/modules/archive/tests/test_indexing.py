"""Testy dopisywania spraw do archiwum (W8).

Sprawdzają trzy warstwy: same adaptery (`add`), serwis indeksujący (kiedy
wolno indeksować) oraz ścieżkę HTTP — zamknięcie wniosku musi być widoczne
w wyszukiwaniu archiwalnym.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.real.archive import VectorArchiveSearch
from app.contracts import (
    ArchiveCase,
    CaseDetail,
    CaseStatus,
    SimilarRequest,
)
from app.core import container
from app.modules.archive.service import ArchiveIndexer, archive_entry


def _entry(case_number: str = "BKS.IV.1431.900.2026", **overrides: object) -> ArchiveCase:
    payload: dict[str, object] = {
        "archive_id": "",
        "case_number": case_number,
        "subject": "Wynagrodzenia pracowników Biura Rady Miasta",
        "year": 2026,
        "request_text": "Wnoszę o udostępnienie informacji o wynagrodzeniach pracowników.",
        "response_text": "Informacja została udostępniona w Biuletynie Informacji Publicznej.",
        "departments": ["wok"],
    }
    payload.update(overrides)
    return ArchiveCase(**payload)  # type: ignore[arg-type]


def _case(status: CaseStatus, **overrides: object) -> CaseDetail:
    from datetime import date, datetime

    now = datetime(2026, 3, 16, 12, 0, 0)
    payload: dict[str, object] = {
        "id": uuid4(),
        "case_number": "BKS.IV.1431.901.2026",
        "ordinal": 901,
        "subject": "Wynagrodzenia pracowników Urzędu Miasta",
        "inflow_date": date(2026, 3, 2),
        "deadline": date(2026, 3, 16),
        "response_date": None,
        "handler_initials": "JK",
        "status": status,
        "year": 2026,
        "days_remaining": 0,
        "urgency": "today",
        "created_at": now,
        "updated_at": now,
    }
    payload.update(overrides)
    return CaseDetail(**payload)  # type: ignore[arg-type]


# ─────────────────────────────── atrapa ─────────────────────────────────────
def test_fake_add_powiększa_archiwum() -> None:
    archive = FakeArchiveSearch()
    before = archive.size()

    archive_id = archive.add(_entry())

    assert archive.size() == before + 1
    assert archive_id.startswith("n")
    assert archive.get(archive_id).case_number == "BKS.IV.1431.900.2026"


def test_fake_add_jest_idempotentne_względem_numeru_sprawy() -> None:
    archive = FakeArchiveSearch()
    first = archive.add(_entry())
    second = archive.add(_entry())

    assert first == second
    assert archive.size() == len(archive._rows)


def test_fake_add_nie_koliduje_z_identyfikatorami_fixtures() -> None:
    archive = FakeArchiveSearch()
    archive_id = archive.add(_entry())

    assert archive_id not in {"a0001", "a0049"}
    assert archive.get(archive_id).subject.startswith("Wynagrodzenia")


def test_dopisana_sprawa_jest_znajdowana_w_wyszukiwaniu() -> None:
    archive = FakeArchiveSearch()
    archive.add(
        _entry(
            case_number="BKS.IV.1431.902.2026",
            subject="Dezynfekcja pomieszczeń biurowych po remoncie",
            request_text="Proszę o informację o środkach do dezynfekcji pomieszczeń.",
        )
    )

    results = archive.similar(SimilarRequest(text="dezynfekcja pomieszczeń", k=5))

    assert results
    assert results[0].case_number == "BKS.IV.1431.902.2026"


# ────────────────────────────── adapter realny ──────────────────────────────
@pytest.fixture
def real_engine(tmp_path: Path) -> Iterator[Engine]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'archive.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    yield engine
    engine.dispose()


def test_real_add_przetrwa_restart(real_engine: Engine) -> None:
    first = VectorArchiveSearch(engine=real_engine)
    archive_id = first.add(_entry())

    second = VectorArchiveSearch(engine=real_engine)

    assert second.size() == first.size()
    assert second.get(archive_id).case_number == "BKS.IV.1431.900.2026"


def test_real_add_jest_idempotentne(real_engine: Engine) -> None:
    archive = VectorArchiveSearch(engine=real_engine)
    first = archive.add(_entry())
    second = archive.add(_entry())

    assert first == second
    assert archive.size() == len(archive._rows)


def test_real_dopisana_sprawa_jest_znajdowana(real_engine: Engine) -> None:
    archive = VectorArchiveSearch(engine=real_engine)
    archive.add(
        _entry(
            case_number="BKS.IV.1431.903.2026",
            subject="Dezynfekcja pomieszczeń biurowych po remoncie",
            request_text="Proszę o informację o środkach do dezynfekcji pomieszczeń.",
        )
    )

    results = archive.similar(SimilarRequest(text="dezynfekcja pomieszczeń", k=5))

    assert results
    assert results[0].case_number == "BKS.IV.1431.903.2026"


def test_real_nie_dotyka_bazy_gdy_podano_rows(real_engine: Engine) -> None:
    """Jawny `rows` wyłącza trwałość — testy nie mogą zależeć od stanu dysku."""
    archive = VectorArchiveSearch(engine=real_engine, rows=[])
    archive.add(_entry())

    assert archive.size() == 1
    assert VectorArchiveSearch(engine=real_engine).size() > 1


# ──────────────────────────────── serwis ────────────────────────────────────
def test_serwis_pomija_sprawy_otwarte() -> None:
    archive = FakeArchiveSearch()
    indexer = ArchiveIndexer(archive)

    assert indexer.index(_case(CaseStatus.PRZYGOTOWANA_ODPOWIEDZ)) is None
    assert archive.size() == len(FakeArchiveSearch()._rows)


def test_serwis_indeksuje_sprawę_zamkniętą() -> None:
    archive = FakeArchiveSearch()
    indexer = ArchiveIndexer(archive)

    archive_id = indexer.index(_case(CaseStatus.ODPOWIEDZ_WYSLANA))

    assert archive_id is not None
    assert archive.get(archive_id).case_number == "BKS.IV.1431.901.2026"


def test_wpis_bierze_notatki_jako_treść_wniosku() -> None:
    case = _case(CaseStatus.ODPOWIEDZ_WYSLANA, notes="Treść wniosku o wynagrodzenia.")

    entry = archive_entry(case)

    assert entry.request_text == "Treść wniosku o wynagrodzenia."
    assert entry.departments == []


def test_wpis_bez_notatek_używa_tematu() -> None:
    case = _case(CaseStatus.ODPOWIEDZ_WYSLANA, notes=None)

    entry = archive_entry(case)

    assert entry.request_text == case.subject


def test_serwis_nie_wywraca_się_gdy_archiwum_zawiedzie() -> None:
    class _Broken:
        def add(self, case: ArchiveCase) -> str:
            raise RuntimeError("baza padła")

    assert ArchiveIndexer(_Broken()).index(_case(CaseStatus.ODPOWIEDZ_WYSLANA)) is None  # type: ignore[arg-type]


# ──────────────────────────────── ścieżka HTTP ──────────────────────────────
@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import app

    container.reset()
    yield TestClient(app)
    container.reset()


def _zamknij_sprawe(client: TestClient) -> dict[str, object]:
    created = client.post(
        "/api/cases",
        json={
            "case_number": "BKS.IV.1431.904.2026",
            "subject": "Dezynfekcja pomieszczeń biurowych po remoncie",
            "inflow_date": "2026-03-02",
            "deadline": "2026-03-16",
            "handler_initials": "JK",
        },
    )
    assert created.status_code == 201, created.text
    case_id = created.json()["id"]

    for status in ("zapytania_wyslane", "przygotowana_odpowiedz", "odpowiedz_wyslana"):
        response = client.post(
            f"/api/cases/{case_id}/transition", json={"to": status}
        )
        assert response.status_code == 200, response.text
    return created.json()


def test_zamkniecie_wniosku_dopisuje_go_do_archiwum(client: TestClient) -> None:
    before = client.post(
        "/api/archive/similar", json={"text": "dezynfekcja pomieszczeń", "k": 5}
    ).json()

    _zamknij_sprawe(client)

    after = client.post(
        "/api/archive/similar", json={"text": "dezynfekcja pomieszczeń", "k": 5}
    ).json()

    assert len(after) >= len(before)
    assert any(
        row["case_number"] == "BKS.IV.1431.904.2026" for row in after
    ), "zamknięty wniosek nie pojawił się w archiwum"


def test_zamkniecie_wniosku_jest_widoczne_przez_get(client: TestClient) -> None:
    _zamknij_sprawe(client)

    results = client.post(
        "/api/archive/similar", json={"text": "dezynfekcja pomieszczeń", "k": 5}
    ).json()
    archive_id = next(
        row["archive_id"]
        for row in results
        if row["case_number"] == "BKS.IV.1431.904.2026"
    )

    detail = client.get(f"/api/archive/{archive_id}")

    assert detail.status_code == 200
    assert detail.json()["subject"] == "Dezynfekcja pomieszczeń biurowych po remoncie"
