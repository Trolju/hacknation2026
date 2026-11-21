"""Atrapa anonimizacji — deterministyczne detektory regułowe.

Baseline o wysokiej precyzji na numerach identyfikacyjnych, uzupełniony
gazetteerem imion, wzorcami tytułów służbowych i form prawnych spółek.
Implementacja produkcyjna (WS6) dokłada NER spaCy i przebieg kontekstowy LLM,
ale nie może pogorszyć precyzji na numerach (zakaz FP na numerach wniosków).
"""

from __future__ import annotations

import re

from app.adapters.fakes import fixtures
from app.contracts import (
    AnonymizerMetrics,
    ApplyRequest,
    ApplyResult,
    CategoryMetrics,
    DetectRequest,
    Span,
    SpanCategory,
)

# ── gazetteer imion (formy podstawowe i odmienione) ──
_FIRST_NAMES: dict[str, tuple[str, ...]] = {
    "Adam": ("Adama", "Adamowi"),
    "Aleksandra": ("Aleksandry", "Aleksandrze", "Aleksandrę", "Aleksandrą"),
    "Andrzej": ("Andrzeja", "Andrzejowi"),
    "Anna": ("Anny", "Annie", "Annę", "Anną"),
    "Barbara": ("Barbary", "Barbarze", "Barbarę", "Barbarą"),
    "Beata": ("Beaty", "Beacie", "Beatę"),
    "Dariusz": ("Dariusza", "Dariuszowi"),
    "Dorota": ("Doroty", "Dorocie", "Dorotę"),
    "Ewa": ("Ewy", "Ewie", "Ewę", "Ewą"),
    "Grzegorz": ("Grzegorza", "Grzegorzowi"),
    "Grażyna": ("Grażyny", "Grażynie", "Grażynę", "Grażyną"),
    "Halina": ("Haliny", "Halinie", "Halinę"),
    "Iwona": ("Iwony", "Iwonie", "Iwonę"),
    "Jakub": ("Jakuba", "Jakubowi"),
    "Jan": ("Jana", "Janowi", "Janem", "Janie"),
    "Janina": ("Janiny", "Janinie", "Janinę"),
    "Jerzy": ("Jerzego", "Jerzemu"),
    "Joanna": ("Joanny", "Joannie", "Joannę", "Joanną"),
    "Józef": ("Józefa", "Józefowi"),
    "Katarzyna": ("Katarzyny", "Katarzynie", "Katarzynę", "Katarzyną"),
    "Krzysztof": ("Krzysztofa", "Krzysztofowi", "Krzysztofem"),
    "Łukasz": ("Łukasza", "Łukaszowi", "Łukaszem"),
    "Magdalena": ("Magdaleny", "Magdalenie", "Magdalenę"),
    "Małgorzata": ("Małgorzaty", "Małgorzacie", "Małgorzatę"),
    "Marcin": ("Marcina", "Marcinowi"),
    "Maria": ("Marii", "Marię", "Marią"),
    "Marek": ("Marka", "Markowi"),
    "Marta": ("Marty", "Marcie", "Martę"),
    "Michał": ("Michała", "Michałowi", "Michałem"),
    "Monika": ("Moniki", "Monice", "Monikę"),
    "Paweł": ("Pawła", "Pawłowi"),
    "Piotr": ("Piotra", "Piotrowi", "Piotrem"),
    "Rafał": ("Rafała", "Rafałowi"),
    "Robert": ("Roberta", "Robertowi"),
    "Roman": ("Romana", "Romanowi"),
    "Stanisław": ("Stanisława", "Stanisławowi"),
    "Tadeusz": ("Tadeusza", "Tadeuszowi"),
    "Tomasz": ("Tomasza", "Tomaszowi", "Tomaszem"),
    "Wojciech": ("Wojciecha", "Wojciechowi"),
    "Zbigniew": ("Zbigniewa", "Zbigniewowi"),
    "Zofia": ("Zofii", "Zofię", "Zofią"),
}

_NAME_FORMS = sorted(
    {form for forms in _FIRST_NAMES.values() for form in forms}
    | set(_FIRST_NAMES),
    key=len,
    reverse=True,
)
_NAME_ALT = "|".join(re.escape(n) for n in _NAME_FORMS)

# Tytuły i funkcje poprzedzające imię — wchodzą w zakres anonimizacji.
_TITLE = (
    r"(?:inż\.|mgr|dr|prof\.|"
    r"starsz(?:y|a|ego|ej)\s+inspektor(?:a)?|inspektor(?:a)?|"
    r"(?:Dyrektor(?:a)?|Naczelnik(?:a)?|Kierownik(?:a)?|Zastęp(?:ca|cy))"
    r"\s+Wydziału(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]+)*)"
)

_LEGAL_FORM = (
    r"(?:Sp\.\s*z\s*o\.o\.|sp\.\s*z\s*o\.o\.|S\.A\.|"
    r"spółka\s+z\s+ograniczoną\s+odpowiedzialnością)"
)

PATTERNS: list[tuple[SpanCategory, re.Pattern[str], float]] = [
    (
        SpanCategory.IBAN,
        re.compile(r"\bPL\d{2}(?:[ ]?\d{4}){6}\b"),
        0.98,
    ),
    (
        SpanCategory.EMAIL,
        re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"),
        0.97,
    ),
    (
        SpanCategory.PESEL,
        re.compile(r"(?<!\d)\b\d{11}\b(?!\d)"),
        0.95,
    ),
    (
        SpanCategory.NIP,
        re.compile(r"(?<!\d)\b\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}\b(?!\d)"),
        0.9,
    ),
    (
        SpanCategory.REGON,
        re.compile(r"(?<!\d)\b\d{9}\b(?!\d)"),
        0.85,
    ),
    (
        SpanCategory.DOWOD,
        re.compile(r"\b[A-Z]{3}[ ]?\d{6}\b"),
        0.9,
    ),
    (
        SpanCategory.PASZPORT,
        re.compile(r"\b[A-Z]{2}\d{7}\b"),
        0.88,
    ),
    (
        SpanCategory.TELEFON,
        # wymagany separator lub prefiks +48 — inaczej 9 cyfr to REGON
        re.compile(
            r"(?:\+48[ -]?)?(?:\d{3}[ -]\d{3}[ -]\d{3}|\d{2}[ -]\d{3}[ -]\d{2}[ -]\d{2})"
        ),
        0.9,
    ),
    (
        SpanCategory.ADRES,
        re.compile(
            r"(?:ul|al|pl|os)\.\s?[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż.-]+"
            r"(?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż.-]+)*\s+\d+[a-zA-Z]?(?:/\d+)?"
            r"(?:,\s*\d{2}-\d{3}\s+[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]+)?"
            r"|skrytka\s+pocztowa\s+\d+(?:,\s*\d{2}-\d{3}\s+[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]+)?"
        ),
        0.85,
    ),
    (
        SpanCategory.DATA_URODZENIA,
        re.compile(r"\b\d{1,2}\.\d{2}\.\d{4}\b"),
        0.8,
    ),
    (
        SpanCategory.IMIE_NAZWISKO,
        re.compile(
            rf"(?:{_TITLE}\s+)?(?:{_NAME_ALT})\s+[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż-]+"
        ),
        0.85,
    ),
    (
        SpanCategory.IMIE_NAZWISKO,
        re.compile(
            rf"(?!Spółka\b)(?:[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż.-]+\s+){{1,4}}{_LEGAL_FORM}"
        ),
        0.8,
    ),
]

# Numery wniosków i sygnatury — muszą pozostać nietknięte.
CASE_NUMBER = re.compile(r"UDIP\.[\w.]+|ZP\.\d+[\w.]*")

# Data w formacie dd.mm.rrrr jest daną osobową tylko po jednym z tych zwrotów.
_DATE_MARKER = re.compile(r"(?:ur\.|urodzon[ya]|Data urodzenia:)\s*$")


def _overlaps(a: Span, b: Span) -> bool:
    return a.start < b.end and b.start < a.end


def merge(spans: list[Span]) -> list[Span]:
    """Scalanie wg reguł z contracts/domain.md §6."""
    ordered = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    out: list[Span] = []
    for span in ordered:
        if not out:
            out.append(span)
            continue
        last = out[-1]
        if not _overlaps(last, span):
            out.append(span)
            continue
        # nakładanie: wygrywa wyższa pewność, przy remisie regex, potem dłuższy
        rank = {"regex": 2, "ner": 1, "llm": 0}
        better = (span.confidence, rank[span.source], span.end - span.start) > (
            last.confidence,
            rank[last.source],
            last.end - last.start,
        )
        if better:
            out[-1] = span
    return out


class FakeAnonymizer:
    def detect(self, req: DetectRequest) -> list[Span]:
        text = req.text
        allowed = set(req.categories) if req.categories else None
        protected = [(m.start(), m.end()) for m in CASE_NUMBER.finditer(text)]
        found: list[Span] = []
        for category, pattern, confidence in PATTERNS:
            if allowed is not None and category not in allowed:
                continue
            for m in pattern.finditer(text):
                if any(m.start() < pe and ps < m.end() for ps, pe in protected):
                    continue
                if category is SpanCategory.DATA_URODZENIA and not _DATE_MARKER.search(
                    text[max(0, m.start() - 24) : m.start()]
                ):
                    continue
                found.append(
                    Span(
                        start=m.start(),
                        end=m.end(),
                        text=m.group(0),
                        category=category,
                        confidence=confidence,
                        source="regex",
                    )
                )
        return merge(found)

    def apply(self, req: ApplyRequest) -> ApplyResult:
        spans = sorted(req.spans, key=lambda s: s.start, reverse=True)
        text = req.text
        for span in spans:
            text = text[: span.start] + req.placeholder + text[span.end :]
        return ApplyResult(text=text, removed_count=len(spans))

    def evaluate(self) -> AnonymizerMetrics:
        tp = fp = fn = 0
        per: dict[str, list[int]] = {}
        for sample in fixtures.anonymization_samples():
            gold = sample["spans"]
            pred = self.detect(DetectRequest(text=sample["text"]))
            gold_keys = {(g["start"], g["end"], g["category"]) for g in gold}
            pred_keys = {(p.start, p.end, p.category.value) for p in pred}
            for key in gold_keys & pred_keys:
                tp += 1
                per.setdefault(key[2], [0, 0, 0])[0] += 1
            for key in pred_keys - gold_keys:
                fp += 1
                per.setdefault(key[2], [0, 0, 0])[1] += 1
            for key in gold_keys - pred_keys:
                fn += 1
                per.setdefault(key[2], [0, 0, 0])[2] += 1
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return AnonymizerMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            per_category={
                cat: CategoryMetrics(
                    precision=round(v[0] / (v[0] + v[1]), 4) if v[0] + v[1] else 0.0,
                    recall=round(v[0] / (v[0] + v[2]), 4) if v[0] + v[2] else 0.0,
                    support=v[0] + v[2],
                )
                for cat, v in per.items()
            },
        )
