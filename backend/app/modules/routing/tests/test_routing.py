"""Testy routingu wydziałowego (WS4).

Sprawdzają adapter realny `KeywordDepartmentRouter`: trafność na ręcznie
napisanym zbiorze oceny, zachowanie brzegowe (puste zapytanie, zapytanie bez
słów kluczowych, `k` spoza kontraktu) oraz treść zapytania do komórek, która
musi powstawać z danych sprawy.
"""

from __future__ import annotations

from datetime import date
from itertools import pairwise
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.fakes import fixtures
from app.adapters.real.routing import (
    KeywordDepartmentRouter,
    build_inquiry_body,
    rank_departments,
)
from app.contracts import CaseDetail, InquiryRequest, SuggestRequest
from app.core import container
from app.core.errors import NotFound, ValidationFailed
from app.modules.routing.evaluation import (
    DATA_PATH,
    EvalCase,
    evaluate,
    load_eval_cases,
)

MIN_TOP1 = 0.80
MIN_TOP3 = 0.80


# ──────────────────────────────── fixtures ──────────────────────────────────
@pytest.fixture(scope="module")
def rows() -> list[dict[str, Any]]:
    return fixtures.departments()


@pytest.fixture(scope="module")
def router() -> KeywordDepartmentRouter:
    return KeywordDepartmentRouter()


@pytest.fixture(scope="module")
def eval_cases() -> list[EvalCase]:
    return load_eval_cases()


def _ranking(text: str) -> list[str]:
    return [scored.department_id for scored in rank_departments(text, fixtures.departments())]


def _case_detail(ordinal: int) -> CaseDetail:
    row = next(item for item in fixtures.cases() if item["ordinal"] == ordinal)
    return container.get_cases().get(UUID(row["id"]))


def _use_real_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODULE_MODE_ROUTING", "real")
    container.reset()


# ────────────────────────────── zbiór oceny ─────────────────────────────────
def test_eval_dataset_is_usable(eval_cases: list[EvalCase]) -> None:
    assert len(eval_cases) == 10
    assert len({case.case_id for case in eval_cases}) == len(eval_cases)
    known = {row["id"] for row in fixtures.departments()}
    for case in eval_cases:
        assert case.expected, case.case_number
        assert set(case.expected) <= known, case.case_number
        assert len(case.why) >= 60, case.case_number


def test_eval_dataset_covers_every_fixture_case(eval_cases: list[EvalCase]) -> None:
    fixture_cases = {row["id"]: row for row in fixtures.cases()}
    assert {case.case_id for case in eval_cases} == set(fixture_cases)
    for case in eval_cases:
        assert case.subject == fixture_cases[case.case_id]["subject"]
        assert case.case_number == fixture_cases[case.case_id]["case_number"]


def test_eval_dataset_lives_in_module() -> None:
    assert DATA_PATH.is_file()
    assert DATA_PATH.parent.name == "data"
    assert DATA_PATH.parent.parent.name == "tests"


def test_top1_accuracy() -> None:
    result = evaluate(_ranking)
    assert result.total == 10
    assert result.top1 >= MIN_TOP1, result.misses


def test_top3_accuracy() -> None:
    result = evaluate(_ranking)
    assert result.top3 >= MIN_TOP3, result.misses


def test_evaluate_reports_misses() -> None:
    """Miara musi umieć pokazać pomyłkę — inaczej nie odróżnia 0.0 od 1.0."""
    result = evaluate(lambda _: ["waiu", "wfin", "wzd"])
    assert result.total == 10
    assert result.top3 < 1.0
    assert result.misses


# ─────────────────────────────── pewność ────────────────────────────────────
def test_confidence_is_monotonic_in_relevance(rows: list[dict[str, Any]]) -> None:
    for case in fixtures.cases():
        ranked = rank_departments(case["subject"], rows)
        for better, worse in pairwise(ranked):
            assert better.raw >= worse.raw
            if better.raw > worse.raw:
                assert better.confidence > worse.confidence
            else:
                assert better.confidence == worse.confidence


def test_confidence_stays_in_range(rows: list[dict[str, Any]]) -> None:
    for case in fixtures.cases():
        for scored in rank_departments(case["subject"], rows):
            assert 0.0 < scored.confidence <= 1.0


def test_confidence_grows_with_number_of_matches(rows: list[dict[str, Any]]) -> None:
    """Więcej trafionych słów kluczowych = wyższa pewność."""
    single = rank_departments("promocja", rows)[0]
    double = rank_departments("promocja w mediach społecznościowych", rows)[0]
    assert double.department_id == single.department_id == "wpm"
    assert double.confidence > single.confidence


# ───────────────────────────── wagi i uzasadnienie ──────────────────────────
def test_phrase_outranks_single_word(rows: list[dict[str, Any]]) -> None:
    ranked = rank_departments("Decyzje o warunkach zabudowy", rows)
    ids = [scored.department_id for scored in ranked]
    assert ids[0] == "waiu"
    assert "bpra" in ids
    assert ids.index("waiu") < ids.index("bpra")


def test_idf_downweights_keyword_shared_by_many_cells(rows: list[dict[str, Any]]) -> None:
    shared = rank_departments("droga", rows)[0]
    unique = rank_departments("wycinka", rows)[0]
    assert unique.raw > shared.raw


def test_coverage_penalty_lowers_partial_matches(rows: list[dict[str, Any]]) -> None:
    short = rank_departments("decyzja", rows)[0]
    long = next(
        scored
        for scored in rank_departments("decyzje o warunkach zabudowy wydane w kwartale", rows)
        if scored.department_id == "bpra"
    )
    assert long.raw < short.raw


def test_rationale_names_the_matched_phrase(rows: list[dict[str, Any]]) -> None:
    top = rank_departments("Decyzje o warunkach zabudowy wydane w IV kwartale 2025 r.", rows)[0]
    assert "„warunki zabudowy”" in top.rationale
    assert "Pokrycie zapytania" in top.rationale


def test_matched_terms_come_from_fixture_keywords(rows: list[dict[str, Any]]) -> None:
    known = {row["id"]: set(row["keywords"]) for row in rows}
    for case in fixtures.cases():
        for scored in rank_departments(case["subject"], rows):
            assert scored.matched_terms
            assert set(scored.matched_terms) <= known[scored.department_id]


# ────────────────────────────── zachowanie brzegowe ─────────────────────────
@pytest.mark.parametrize("text", ["", "   ", "\n\t", "..."])
def test_empty_query_returns_nothing(router: KeywordDepartmentRouter, text: str) -> None:
    assert router.suggest(SuggestRequest(text=text)) == []


def test_query_without_keywords_returns_nothing(router: KeywordDepartmentRouter) -> None:
    assert router.suggest(SuggestRequest(text="Zażółć gęślą jaźń. Ala ma kota.")) == []


def test_k_is_clamped_inside_adapter(router: KeywordDepartmentRouter) -> None:
    text = "Wydatki na promocję miasta w mediach społecznościowych"
    assert len(router.suggest(SuggestRequest(text=text, k=1))) == 1
    assert len(router.suggest(SuggestRequest(text=text, k=10))) <= 10
    # Wartości spoza kontraktu nie mogą wywrócić adaptera.
    assert len(router.suggest(SuggestRequest.model_construct(text=text, k=0))) == 1
    assert len(router.suggest(SuggestRequest.model_construct(text=text, k=99))) <= 10


@pytest.mark.parametrize("k", [0, 11, -3])
def test_k_out_of_contract_range_is_rejected(client: TestClient, k: int) -> None:
    response = client.post("/api/routing/suggest", json={"text": "promocja", "k": k})
    assert response.status_code == 422


def test_departments_match_fixtures(router: KeywordDepartmentRouter) -> None:
    departments = router.departments()
    assert len(departments) == 26
    assert {item.id for item in departments} == {row["id"] for row in fixtures.departments()}


def test_container_resolves_real_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    _use_real_adapter(monkeypatch)
    assert isinstance(container.get_routing(), KeywordDepartmentRouter)


# ──────────────────────────────── zapytanie ─────────────────────────────────
def test_inquiry_uses_case_data(router: KeywordDepartmentRouter) -> None:
    case = fixtures.cases()[5]
    letter = router.inquiry(InquiryRequest(case_id=UUID(case["id"]), department_ids=["waiu"]))
    assert case["case_number"] in letter.body
    assert case["subject"] in letter.body
    assert "24 marca 2026 r." in letter.body
    assert case["case_number"] in letter.title
    assert letter.addressees == ["Wydział Architektury i Urbanistyki"]


def test_inquiry_lists_every_addressee(router: KeywordDepartmentRouter) -> None:
    case = fixtures.cases()[5]
    letter = router.inquiry(
        InquiryRequest(case_id=UUID(case["id"]), department_ids=["waiu", "bpra"])
    )
    assert letter.addressees == ["Wydział Architektury i Urbanistyki", "Biuro Prawne"]
    assert "1. Wydział Architektury i Urbanistyki" in letter.body
    assert "2. Biuro Prawne" in letter.body


def test_inquiry_body_contains_legal_basis_and_deadline() -> None:
    case = _case_detail(6)
    body = build_inquiry_body(
        case, ["Wydział Architektury i Urbanistyki"], reference=date(2026, 3, 16)
    )
    assert "art. 13 ust. 1" in body
    assert "o dostępie do informacji publicznej" in body
    assert "24 marca 2026 r." in body
    assert "21 marca 2026 r." in body
    assert "14 dni od dnia wpływu" in body
    assert "Urząd Miasta Bydgoszczy" in body
    # Data kończy się skrótem „r.”, więc po niej nie może stać druga kropka.
    assert "r.." not in body


def test_inquiry_body_marks_overdue_deadline() -> None:
    case = _case_detail(7)
    body = build_inquiry_body(case, ["Biuro Rady Miasta"], reference=date(2026, 3, 16))
    assert "upłynął 24 lutego 2026 r." in body


def test_inquiry_unknown_case_raises_not_found(router: KeywordDepartmentRouter) -> None:
    with pytest.raises(NotFound):
        router.inquiry(InquiryRequest(case_id=uuid4(), department_ids=["waiu"]))


def test_inquiry_unknown_department_raises_not_found(router: KeywordDepartmentRouter) -> None:
    case_id = UUID(fixtures.cases()[0]["id"])
    with pytest.raises(NotFound):
        router.inquiry(InquiryRequest(case_id=case_id, department_ids=["nie-ma-takiej"]))


def test_inquiry_without_departments_is_rejected(router: KeywordDepartmentRouter) -> None:
    case_id = UUID(fixtures.cases()[0]["id"])
    with pytest.raises(ValidationFailed):
        router.inquiry(InquiryRequest(case_id=case_id, department_ids=[]))


# ──────────────────────────────── przez API ─────────────────────────────────
def test_api_suggest_is_sorted_by_confidence(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_real_adapter(monkeypatch)
    rows = client.post(
        "/api/routing/suggest",
        json={"text": "Decyzje o warunkach zabudowy wydane w IV kwartale 2025 r.", "k": 3},
    ).json()
    assert rows[0]["department_id"] == "waiu"
    confidences = [row["confidence"] for row in rows]
    assert confidences == sorted(confidences, reverse=True)


def test_api_inquiry_returns_letter_from_case(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_real_adapter(monkeypatch)
    case = fixtures.cases()[5]
    body = client.post(
        "/api/routing/inquiry",
        json={"case_id": case["id"], "department_ids": ["waiu", "bpra"]},
    ).json()
    assert case["case_number"] in body["body"]
    assert case["subject"] in body["body"]
    assert body["addressees"] == ["Wydział Architektury i Urbanistyki", "Biuro Prawne"]


def test_api_inquiry_unknown_case_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_real_adapter(monkeypatch)
    response = client.post(
        "/api/routing/inquiry",
        json={"case_id": str(uuid4()), "department_ids": ["waiu"]},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_api_inquiry_unknown_department_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_real_adapter(monkeypatch)
    response = client.post(
        "/api/routing/inquiry",
        json={"case_id": fixtures.cases()[0]["id"], "department_ids": ["nie-ma-takiej"]},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_api_departments_work_in_real_mode(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_real_adapter(monkeypatch)
    rows = client.get("/api/routing/departments").json()
    assert len(rows) == 26
    assert all(row["id"] and row["name"] for row in rows)


def test_fake_adapter_still_serves_default_mode(client: TestClient) -> None:
    """Atrapa zostaje i dalej działa — tryb domyślny to `fake`."""
    assert not isinstance(container.get_routing(), KeywordDepartmentRouter)
    rows = client.post(
        "/api/routing/suggest", json={"text": "wynagrodzenia pracowników", "k": 3}
    ).json()
    assert rows and rows[0]["confidence"] <= 1.0
