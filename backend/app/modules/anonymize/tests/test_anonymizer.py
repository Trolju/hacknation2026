"""Testy adaptera realnego anonimizacji (WS6).

Zbiór `fixtures/anonymization/labeled.jsonl` jest tylko testem dymnym — reguły
atrapy były do niego dostrajane. Właściwą miarą jakości jest ręcznie napisany
zbiór `data/heldout.jsonl`: inne nazwiska, ulice, miasta i konstrukcje zdaniowe.
Uwaga metodologiczna: zbiór i reguły powstały w tym samym module, więc 1.0 na
held-out jest górnym oszacowaniem, a nie niezależnym pomiarem.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.adapters.real.anonymize import NerAnonymizer, merge_spans
from app.contracts import (
    ApplyRequest,
    DetectRequest,
    Span,
    SpanCategory,
)
from app.modules.anonymize.metrics import (
    HELDOUT_PATH,
    error_report,
    evaluate_samples,
    load_heldout,
)

MIN_PRECISION = 0.90
MIN_RECALL = 0.85

# Numery wniosków i sygnatury postępowań — nie są danymi osobowymi.
CASE_NUMBER = re.compile(r"\bBKS\.IV\.1431\.[0-9A-Za-z.]+|\bZP\.[0-9A-Za-z.]+")

NUMERIC_CATEGORIES = {
    SpanCategory.NIP,
    SpanCategory.REGON,
    SpanCategory.PESEL,
    SpanCategory.DOWOD,
    SpanCategory.PASZPORT,
    SpanCategory.TELEFON,
    SpanCategory.IBAN,
}


@pytest.fixture(scope="module")
def anonymizer() -> NerAnonymizer:
    return NerAnonymizer()


@pytest.fixture(scope="module")
def heldout() -> list[dict]:
    return load_heldout()


# ──────────────────────────── zbiór held-out ───────────────────────────
def test_heldout_dataset_is_usable(heldout: list[dict]) -> None:
    assert len(heldout) >= 25
    assert len({sample["id"] for sample in heldout}) == len(heldout)
    categories = {category.value for category in SpanCategory}
    for sample in heldout:
        text = sample["text"]
        previous_end = 0
        for span in sample["spans"]:
            assert span["category"] in categories, sample["id"]
            assert 0 <= span["start"] < span["end"] <= len(text), sample["id"]
            assert text[span["start"] : span["end"]] == span["text"], sample["id"]
            assert span["start"] >= previous_end, sample["id"]
            previous_end = span["end"]


def test_heldout_is_not_a_copy_of_fixtures(heldout: list[dict]) -> None:
    fixtures_path = Path(__file__).resolve().parents[5] / "fixtures" / "anonymization"
    fixture_texts = {
        json.loads(line)["text"]
        for line in (fixtures_path / "labeled.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    assert not {sample["text"] for sample in heldout} & fixture_texts


def test_heldout_metrics(anonymizer: NerAnonymizer, heldout: list[dict]) -> None:
    metrics = evaluate_samples(heldout, anonymizer.detect)
    problems = error_report(heldout, anonymizer.detect)
    assert metrics.precision >= MIN_PRECISION, problems
    assert metrics.recall >= MIN_RECALL, problems
    assert metrics.f1 >= 0.85, problems
    assert metrics.per_category, "brak rozbicia na kategorie"


def test_evaluate_reports_heldout(anonymizer: NerAnonymizer, heldout: list[dict]) -> None:
    assert anonymizer.evaluate() == evaluate_samples(heldout, anonymizer.detect)


def test_heldout_path_points_into_module() -> None:
    assert HELDOUT_PATH.exists()
    assert HELDOUT_PATH.parent.name == "data"


# ──────────────────── zakaz fałszywych trafień na numerach ─────────────
CASE_NUMBER_TEXTS = [
    "Wniosek nr BKS.IV.1431.12.2026 wpłynął do urzędu.",
    "Sprawa BKS.IV.1431.123456789.2026 jest w toku.",
    "Postępowanie ZP.271.42.2026 rozstrzygnięto.",
    "Sygnatura ZP.1435.7.2026 dotyczy dostawy sprzętu.",
    "Znak sprawy: BKS.IV.1431.101.2026 oraz ZP.271.15.2026.",
    "Wniosek BKS.IV.1431.88.2026 złożył Sebastian Nowicki, PESEL 92071456789.",
]


@pytest.mark.parametrize("text", CASE_NUMBER_TEXTS)
def test_no_false_positives_on_case_numbers(anonymizer: NerAnonymizer, text: str) -> None:
    protected = [(m.start(), m.end()) for m in CASE_NUMBER.finditer(text)]
    assert protected, "test wymaga numeru wniosku w tekście"
    for span in anonymizer.detect(DetectRequest(text=text)):
        for start, end in protected:
            overlaps = span.start < end and start < span.end
            assert not overlaps, f"{span.category.value} pokrył numer sprawy: {span.text!r}"
        assert span.category not in NUMERIC_CATEGORIES or not any(
            span.start < end and start < span.end for start, end in protected
        )


def test_case_numbers_are_not_numeric_categories(anonymizer: NerAnonymizer) -> None:
    text = "BKS.IV.1431.12345678901.2026 i ZP.271.123456789.2026"
    spans = anonymizer.detect(DetectRequest(text=text))
    assert all(span.category not in NUMERIC_CATEGORIES for span in spans)


# ──────────────────────────── scalanie spanów ──────────────────────────
def _span(start: int, end: int, category: SpanCategory, confidence: float, source: str) -> Span:
    return Span(
        start=start,
        end=end,
        text="x" * (end - start),
        category=category,
        confidence=confidence,
        source=source,  # type: ignore[arg-type]
    )


def test_merge_prefers_higher_confidence() -> None:
    low = _span(0, 10, SpanCategory.ADRES, 0.5, "ner")
    high = _span(2, 8, SpanCategory.ADRES, 0.9, "regex")
    assert merge_spans([low, high]) == [high]


def test_merge_prefers_regex_on_tie() -> None:
    ner = _span(0, 10, SpanCategory.IMIE_NAZWISKO, 0.8, "ner")
    regex = _span(0, 10, SpanCategory.IMIE_NAZWISKO, 0.8, "regex")
    assert merge_spans([ner, regex]) == [regex]


def test_merge_prefers_longer_on_tie() -> None:
    short = _span(0, 5, SpanCategory.ADRES, 0.8, "regex")
    long = _span(0, 12, SpanCategory.ADRES, 0.8, "regex")
    assert merge_spans([short, long]) == [long]


def test_merge_absorbs_contained_span() -> None:
    outer = _span(0, 20, SpanCategory.ADRES, 0.9, "regex")
    inner = _span(5, 10, SpanCategory.ADRES, 0.9, "regex")
    assert merge_spans([inner, outer]) == [outer]


def test_merge_keeps_disjoint_spans_sorted() -> None:
    first = _span(0, 3, SpanCategory.PESEL, 0.9, "regex")
    second = _span(10, 15, SpanCategory.EMAIL, 0.9, "regex")
    assert merge_spans([second, first]) == [first, second]


def test_detect_returns_non_overlapping_spans(anonymizer: NerAnonymizer) -> None:
    text = (
        "Wnioskodawca Jan Kowalski, PESEL 85041212345, ul. Gdańska 42/7, "
        "85-005 Bydgoszcz, tel. +48 601 234 567, e-mail jan@example.com."
    )
    spans = anonymizer.detect(DetectRequest(text=text))
    for previous, current in zip(spans, spans[1:], strict=False):
        assert previous.end <= current.start


# ──────────────────────────── apply ────────────────────────────────────
def test_apply_default_placeholder(anonymizer: NerAnonymizer) -> None:
    text = "Jan Kowalski, PESEL 85041212345."
    spans = anonymizer.detect(DetectRequest(text=text))
    result = anonymizer.apply(ApplyRequest(text=text, spans=spans))
    assert "Kowalski" not in result.text
    assert "85041212345" not in result.text
    assert "[USUNIĘTO]" in result.text
    assert result.removed_count == len(spans)


@pytest.mark.parametrize("placeholder", ["***", "<REDAKCJA>", "…", ""])
def test_apply_with_custom_placeholder(anonymizer: NerAnonymizer, placeholder: str) -> None:
    text = "Kontakt: jan.kowalski@example.com, tel. 601 234 567."
    spans = anonymizer.detect(DetectRequest(text=text))
    result = anonymizer.apply(
        ApplyRequest(text=text, spans=spans, placeholder=placeholder)
    )
    assert "jan.kowalski@example.com" not in result.text
    assert "601 234 567" not in result.text
    assert result.text.count(placeholder) == len(spans) if placeholder else True


def test_apply_merges_overlapping_spans(anonymizer: NerAnonymizer) -> None:
    text = "Jan Kowalski złożył wniosek."
    spans = [
        _span(0, 12, SpanCategory.IMIE_NAZWISKO, 0.9, "regex"),
        _span(4, 12, SpanCategory.IMIE_NAZWISKO, 0.5, "ner"),
    ]
    result = anonymizer.apply(ApplyRequest(text=text, spans=spans, placeholder="X"))
    assert result.text == "X złożył wniosek."
    assert result.removed_count == 1


def test_apply_ignores_out_of_bounds_spans(anonymizer: NerAnonymizer) -> None:
    text = "Krótki tekst."
    spans = [
        _span(0, 6, SpanCategory.INNE, 0.9, "regex"),
        _span(50, 60, SpanCategory.INNE, 0.9, "regex"),
        _span(3, 3, SpanCategory.INNE, 0.9, "regex"),
    ]
    result = anonymizer.apply(ApplyRequest(text=text, spans=spans, placeholder="_"))
    assert result.text == "_ tekst."
    assert result.removed_count == 1


def test_apply_without_spans_returns_input(anonymizer: NerAnonymizer) -> None:
    text = "Bez danych osobowych."
    result = anonymizer.apply(ApplyRequest(text=text, spans=[]))
    assert result.text == text
    assert result.removed_count == 0


# ──────────────────────── filtr kategorii i NER ───────────────────────
def test_detect_respects_category_filter(anonymizer: NerAnonymizer) -> None:
    text = "Jan Kowalski, e-mail jan@example.com, PESEL 85041212345."
    spans = anonymizer.detect(
        DetectRequest(text=text, categories=[SpanCategory.EMAIL])
    )
    assert [span.category for span in spans] == [SpanCategory.EMAIL]


def test_detect_works_without_spacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.adapters.real.anonymize.spacy", None)
    anonymizer = NerAnonymizer()
    spans = anonymizer.detect(DetectRequest(text="Pani Anna Nowak, tel. 601 234 567."))
    assert {span.category for span in spans} == {
        SpanCategory.IMIE_NAZWISKO,
        SpanCategory.TELEFON,
    }


def test_ner_spans_lose_to_regex(anonymizer: NerAnonymizer) -> None:
    text = "Jan Kowalski złożył wniosek."
    regex = _span(0, 12, SpanCategory.IMIE_NAZWISKO, 0.85, "regex")
    ner = _span(0, 12, SpanCategory.IMIE_NAZWISKO, 0.7, "ner")
    assert merge_spans([ner, regex]) == [regex]
    assert anonymizer.detect(DetectRequest(text=text))[0].source == "regex"


# ──────────────────────── rozpoznawanie bez gazetteeru ─────────────────
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Wniosek złożył Pan Zdzisław Kot.", "Zdzisław Kot"),
        ("Wnioskodawczyni Krystyna Bąk prosi o wgląd.", "Krystyna Bąk"),
        ("Protokół podpisał Bartłomiej Zawadzki.", "Bartłomiej Zawadzki"),
        ("Odpowiedź wysłała Pani Wioletta Cichocka.", "Wioletta Cichocka"),
    ],
)
def test_names_without_gazetteer(
    anonymizer: NerAnonymizer, text: str, expected: str
) -> None:
    spans = anonymizer.detect(DetectRequest(text=text))
    names = [span.text for span in spans if span.category is SpanCategory.IMIE_NAZWISKO]
    assert expected in names


def test_address_without_street_prefix(anonymizer: NerAnonymizer) -> None:
    spans = anonymizer.detect(DetectRequest(text="Adres: 87-100 Toruń."))
    assert [span.category for span in spans] == [SpanCategory.ADRES]
    assert spans[0].text == "87-100 Toruń"


def test_land_register_and_court_signature(anonymizer: NerAnonymizer) -> None:
    text = "Sygn. akt II SA/Bd 456/26, księga KW BY1B/00012345/6."
    spans = anonymizer.detect(DetectRequest(text=text))
    assert {span.category for span in spans} == {SpanCategory.INNE}
    assert {span.text for span in spans} == {
        "Sygn. akt II SA/Bd 456/26",
        "KW BY1B/00012345/6",
    }


def test_institution_names_are_not_personal_data(anonymizer: NerAnonymizer) -> None:
    text = (
        "Zarząd Dróg Miejskich i Komunikacji Publicznej w Bydgoszczy oraz "
        "Wydział Gospodarki Komunalnej i Referat Kontroli."
    )
    assert anonymizer.detect(DetectRequest(text=text)) == []


# ──────────────────────────── kontener ─────────────────────────────────
def test_container_uses_real_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import container

    monkeypatch.setenv("MODULE_MODE_ANONYMIZE", "real")
    container.reset()
    try:
        assert isinstance(container.get_anonymizer(), NerAnonymizer)
    finally:
        container.reset()


# ──────────────────────── przebieg NER (spaCy) ─────────────────────────
class _StubNer:
    """Podstawiony detektor osób — pozwala testować scalanie bez modelu."""

    def person_spans(self, text: str) -> list[Span]:
        return [
            Span(
                start=0,
                end=12,
                text=text[0:12],
                category=SpanCategory.IMIE_NAZWISKO,
                confidence=0.7,
                source="ner",
            )
        ]


def test_ner_spans_are_merged_with_regex() -> None:
    anonymizer = NerAnonymizer(ner=_StubNer())
    spans = anonymizer.detect(DetectRequest(text="Jan Kowalski złożył wniosek."))
    assert len(spans) == 1
    assert spans[0].source == "regex"


def test_ner_only_span_survives_when_regex_misses() -> None:
    anonymizer = NerAnonymizer(ner=_StubNer())
    spans = anonymizer.detect(DetectRequest(text="Zyxwvut Qqqqqq złożył wniosek."))
    assert len(spans) == 1
    assert spans[0].source == "ner"


def test_spacy_loader_degrades_when_model_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BrokenSpacy:
        @staticmethod
        def load(_name: str) -> object:
            raise OSError("brak modelu")

    monkeypatch.setattr("app.adapters.real.anonymize.spacy", _BrokenSpacy)
    from app.adapters.real.anonymize import _SpacyNer

    ner = _SpacyNer()
    assert ner.available is False
    assert ner.person_spans("Jan Kowalski") == []
