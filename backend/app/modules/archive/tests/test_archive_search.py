"""Testy adaptera `VectorArchiveSearch` — jakość wyszukiwania i przypadki brzegowe.

Miary liczone są na zbiorze oceny `tests/data/queries.json`. Baseline to atrapa
`FakeArchiveSearch` (TF-IDF + kosinus) liczona w tym samym teście na tych samych
danych — dzięki temu porównanie nie zależy od tego, jak wygląda fixtures.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import Engine, create_engine

from app.adapters.fakes import fixtures
from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.real.archive import (
    MIN_SCORE,
    VectorArchiveSearch,
    archive_case_uuid,
    fold,
    stem,
    tokenize,
)
from app.contracts import SimilarRequest
from app.core.errors import NotFound

DATA_DIR = Path(__file__).parent / "data"

RECALL_THRESHOLD = 0.80
MRR_THRESHOLD = 0.70


# ──────────────────────────────── pomocnicze ────────────────────────────────
def _ids(results: Sequence[Any]) -> list[str]:
    return [item.archive_id for item in results]


def _evaluate(search: Any, queries: list[dict[str, Any]], k: int = 5) -> tuple[float, float]:
    """Zwraca (recall@k, MRR) uśrednione po zapytaniach zbioru oceny."""
    recalls: list[float] = []
    reciprocal: list[float] = []
    for query in queries:
        expected = set(query["expected"])
        found = _ids(search.similar(SimilarRequest(text=query["text"], k=k)))
        recalls.append(len(expected & set(found[:k])) / len(expected))
        reciprocal.append(
            next(
                (1.0 / (position + 1) for position, aid in enumerate(found) if aid in expected),
                0.0,
            )
        )
    return sum(recalls) / len(recalls), sum(reciprocal) / len(reciprocal)


class _BrokenEmbedding:
    """Model, który zawsze zawodzi — symuluje brak sieci i brak wag."""

    dim = 384

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("model niedostępny")


class _CountingEmbedding:
    """Opakowanie atrapy — liczy, ile tekstów trafiło do modelu."""

    def __init__(self) -> None:
        from app.adapters.fakes.inference import FakeEmbedding

        self._inner = FakeEmbedding()
        self.calls: list[int] = []

    @property
    def dim(self) -> int:
        return self._inner.dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(len(texts))
        return self._inner.embed(texts)


# ──────────────────────────────── zbiór oceny ───────────────────────────────
def test_eval_set_is_well_formed(eval_queries: list[dict[str, Any]]) -> None:
    known = {row["archive_id"] for row in fixtures.archive()}
    subjects = {row["subject"] for row in fixtures.archive()}

    assert len(eval_queries) >= 20
    assert len({query["id"] for query in eval_queries}) == len(eval_queries)
    for query in eval_queries:
        assert query["text"].strip(), query["id"]
        assert query["expected"], query["id"]
        assert set(query["expected"]) <= known, query["id"]
        assert query["text"] not in subjects, query["id"]


def test_recall_at_5_meets_threshold(
    search: VectorArchiveSearch, eval_queries: list[dict[str, Any]]
) -> None:
    recall, _ = _evaluate(search, eval_queries)

    assert recall >= RECALL_THRESHOLD, f"recall@5 = {recall:.3f}"


def test_mrr_meets_threshold(
    search: VectorArchiveSearch, eval_queries: list[dict[str, Any]]
) -> None:
    _, mrr = _evaluate(search, eval_queries)

    assert mrr >= MRR_THRESHOLD, f"MRR = {mrr:.3f}"


def test_recall_beats_tfidf_baseline(
    search: VectorArchiveSearch, eval_queries: list[dict[str, Any]]
) -> None:
    """Adapter musi być lepszy od atrapy TF-IDF na tym samym zbiorze oceny."""
    ours, our_mrr = _evaluate(search, eval_queries)
    baseline, baseline_mrr = _evaluate(FakeArchiveSearch(), eval_queries)

    assert ours > baseline, f"hybryda {ours:.3f} vs baseline {baseline:.3f}"
    assert our_mrr > baseline_mrr, f"MRR {our_mrr:.3f} vs baseline {baseline_mrr:.3f}"


# ────────────────────────────── normalizacja ────────────────────────────────
@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("wynagrodzenia", "wynagrodzeń"),
        ("premie", "premii"),
        ("diety", "diet"),
        ("radnym", "radnych"),
        ("pracownicy", "pracowników"),
        ("kamer", "kamery"),
        ("umowy", "umów"),
        ("miasta", "miast"),
    ],
)
def test_stemmer_scala_formy_fleksyjne(left: str, right: str) -> None:
    assert stem(fold(left)) == stem(fold(right))


def test_fold_usuwa_diakrytyki() -> None:
    assert fold("Wynagrodzeń ŁÓDŹ") == "wynagrodzen lodz"


def test_tokenize_odrzuca_stopliste_i_formuly_udip() -> None:
    tokens = tokenize(
        "Zwracam się z wnioskiem o udostępnienie informacji publicznej o diety radnych"
    )

    assert "diet" in tokens
    assert "radn" in tokens
    assert "wniosk" not in tokens
    assert "informacj" not in tokens


def test_tokenize_zachowuje_lata() -> None:
    assert "2024" in tokenize("wydatki w 2024 roku")


# ──────────────────────────────── przypadki brzegowe ────────────────────────
def test_empty_query_returns_nothing(search: VectorArchiveSearch) -> None:
    assert search.similar(SimilarRequest(text="", k=5)) == []


def test_whitespace_query_returns_nothing(search: VectorArchiveSearch) -> None:
    assert search.similar(SimilarRequest(text="   \n\t  ", k=5)) == []


def test_query_without_hits_returns_empty_list(search: VectorArchiveSearch) -> None:
    results = search.similar(SimilarRequest(text="xyzzy plugh qwertyuiop", k=5))

    assert results == []


def test_query_of_only_stopwords_returns_empty_list(search: VectorArchiveSearch) -> None:
    results = search.similar(
        SimilarRequest(text="proszę o udostępnienie informacji publicznej", k=5)
    )

    assert results == []


@pytest.mark.parametrize("k", [0, -1, 21, 100])
def test_k_outside_range_is_rejected(k: int) -> None:
    with pytest.raises(ValidationError):
        SimilarRequest(text="diety radnych", k=k)


def test_k_limits_number_of_results(search: VectorArchiveSearch) -> None:
    one = search.similar(SimilarRequest(text="wydatki miasta na sport i kulturę", k=1))
    five = search.similar(SimilarRequest(text="wydatki miasta na sport i kulturę", k=5))

    assert len(one) == 1
    assert len(five) <= 5
    assert len(five) > len(one)


def test_results_are_sorted_by_score_and_bounded(search: VectorArchiveSearch) -> None:
    results = search.similar(SimilarRequest(text="koszty utrzymania monitoringu miejskiego", k=10))

    assert results
    scores = [item.score for item in results]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 for score in scores)
    assert all(score >= MIN_SCORE for score in scores)


def test_year_from_filters_older_cases(search: VectorArchiveSearch) -> None:
    text = "koszty utrzymania monitoringu miejskiego"

    assert search.similar(SimilarRequest(text=text, k=5, year_from=2025))
    assert search.similar(SimilarRequest(text=text, k=5, year_from=2026)) == []


def test_exclude_case_id_removes_that_case(search: VectorArchiveSearch) -> None:
    text = "koszty utrzymania monitoringu miejskiego"
    baseline = _ids(search.similar(SimilarRequest(text=text, k=5)))
    assert "a0026" in baseline

    filtered = _ids(
        search.similar(
            SimilarRequest(text=text, k=5, exclude_case_id=archive_case_uuid("a0026"))
        )
    )

    assert "a0026" not in filtered
    # Wykluczenie zwalnia miejsce w rankingu, ale nie zmienia kolejności pozostałych.
    assert set(baseline) - {"a0026"} <= set(filtered)


def test_exclude_case_id_of_unknown_case_changes_nothing(search: VectorArchiveSearch) -> None:
    text = "koszty utrzymania monitoringu miejskiego"

    plain = _ids(search.similar(SimilarRequest(text=text, k=5)))
    other = _ids(search.similar(SimilarRequest(text=text, k=5, exclude_case_id=uuid4())))

    assert plain == other


def test_get_returns_full_archive_case(search: VectorArchiveSearch) -> None:
    case = search.get("a0001")

    assert case.archive_id == "a0001"
    assert case.case_number == "BKS.IV.1431.87.2025"
    assert case.year == 2025
    assert case.request_text
    assert case.response_text
    assert case.departments


def test_get_unknown_id_raises_not_found(search: VectorArchiveSearch) -> None:
    with pytest.raises(NotFound) as excinfo:
        search.get("a9999")

    assert excinfo.value.status_code == 404
    assert excinfo.value.code == "not_found"
    assert excinfo.value.message == "Nie znaleziono sprawy archiwalnej."


def test_size_matches_fixtures(search: VectorArchiveSearch) -> None:
    assert search.size() == len(fixtures.archive())


def test_results_carry_terms_and_excerpts(search: VectorArchiveSearch) -> None:
    results = search.similar(SimilarRequest(text="diety wypłacane radnym", k=3))

    assert results
    top = results[0]
    assert top.archive_id == "a0028"
    assert top.matched_terms
    assert all(term and term == term.lower() for term in top.matched_terms)
    assert top.snippet
    assert top.response_excerpt
    assert len(top.snippet) <= 241
    assert len(top.response_excerpt) <= 241


def test_matched_terms_are_query_words_not_stems(search: VectorArchiveSearch) -> None:
    results = search.similar(SimilarRequest(text="diety wypłacane radnym", k=1))

    assert "diety" in results[0].matched_terms


# ──────────────────────────────── tryb offline ──────────────────────────────
def test_works_when_embedding_model_is_unavailable(engine: Engine) -> None:
    search = VectorArchiveSearch(embedding=_BrokenEmbedding(), engine=engine)

    results = search.similar(SimilarRequest(text="diety wypłacane radnym", k=5))

    assert results
    assert results[0].archive_id == "a0028"


def test_offline_results_stay_sensible_on_eval_set(
    engine: Engine, eval_queries: list[dict[str, Any]]
) -> None:
    """Bez modeli wyszukiwanie dalej spełnia próg jakości."""
    search = VectorArchiveSearch(embedding=_BrokenEmbedding(), engine=engine)

    recall, _ = _evaluate(search, eval_queries)

    assert recall >= RECALL_THRESHOLD, f"recall@5 offline = {recall:.3f}"


def test_fake_embedding_does_not_pollute_ranking(
    engine: Engine, eval_queries: list[dict[str, Any]]
) -> None:
    """Atrapa embeddingów daje kosinusy z szumu — kanał musi być wyłączony."""
    with_fake = VectorArchiveSearch(engine=engine)
    without = VectorArchiveSearch(embedding=_BrokenEmbedding(), engine=engine)

    fake_recall, _ = _evaluate(with_fake, eval_queries)
    offline_recall, _ = _evaluate(without, eval_queries)

    assert fake_recall >= offline_recall


# ──────────────────────────────── cache wektorów ────────────────────────────
def _document_batches(embedding: _CountingEmbedding) -> list[int]:
    """Wywołania modelu dla spraw archiwalnych (zapytanie to zawsze jeden tekst)."""
    total = len(fixtures.archive())
    return [count for count in embedding.calls if count == total]


def test_embeddings_are_computed_once_and_cached(engine: Engine) -> None:
    embedding = _CountingEmbedding()
    search = VectorArchiveSearch(embedding=embedding, engine=engine)

    search.similar(SimilarRequest(text="diety radnych", k=3))
    search.similar(SimilarRequest(text="koszty monitoringu", k=3))

    # Pierwsze zapytanie liczy wektory wszystkich spraw, drugie już ich nie rusza.
    assert _document_batches(embedding) == [len(fixtures.archive())]


def test_embedding_cache_survives_new_instance(engine: Engine) -> None:
    first = _CountingEmbedding()
    VectorArchiveSearch(embedding=first, engine=engine).similar(
        SimilarRequest(text="diety radnych", k=3)
    )

    second = _CountingEmbedding()
    VectorArchiveSearch(embedding=second, engine=engine).similar(
        SimilarRequest(text="diety radnych", k=3)
    )

    assert _document_batches(first) == [len(fixtures.archive())]
    assert _document_batches(second) == []


def test_cache_is_keyed_by_model(engine: Engine) -> None:
    class _OtherEmbedding(_CountingEmbedding):
        pass

    VectorArchiveSearch(embedding=_CountingEmbedding(), engine=engine).similar(
        SimilarRequest(text="diety radnych", k=3)
    )

    other = _OtherEmbedding()
    VectorArchiveSearch(embedding=other, engine=engine).similar(
        SimilarRequest(text="diety radnych", k=3)
    )

    assert _document_batches(other) == [len(fixtures.archive())]


def test_search_works_when_cache_write_fails(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Baza tylko do odczytu nie może wywrócić wyszukiwania."""
    search = VectorArchiveSearch(engine=engine)

    def refuse(*_: object, **__: object) -> None:
        raise RuntimeError("baza tylko do odczytu")

    monkeypatch.setattr(search, "_store_cached", refuse)

    results = search.similar(SimilarRequest(text="diety radnych", k=3))

    assert results
    assert results[0].archive_id == "a0028"


# ──────────────────────────────── kontener ──────────────────────────────────
def test_container_selects_real_adapter(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from app.core import container, db

    engine = create_engine(f"sqlite:///{tmp_path / 'container.db'}", future=True)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setenv("MODULE_MODE_ARCHIVE", "real")
    container.reset()

    adapter = container.get_archive()

    assert isinstance(adapter, VectorArchiveSearch)
    assert adapter.size() == len(fixtures.archive())
    engine.dispose()


def test_container_falls_back_to_fake_by_default() -> None:
    from app.core import container

    assert isinstance(container.get_archive(), FakeArchiveSearch)


def test_eval_file_is_valid_json() -> None:
    payload = json.loads((DATA_DIR / "queries.json").read_text(encoding="utf-8"))

    assert payload["version"] == 1
    assert payload["description"]
