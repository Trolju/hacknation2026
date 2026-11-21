"""Szablon projektu odpowiedzi — treść, gdy model jest niedostępny.

Szablon jest tym samym pismem, które powstaje przy degradacji: ma podstawę
prawną z przepisów, odniesienia do spraw zbliżonych, stanowiska komórek,
pouczenie i podpis. Każde zdanie merytoryczne niesie odnośnik `[^n]`, więc
projekt z szablonu przechodzi tę samą kontrolę pokrycia co treść z modelu.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import date

from app.contracts import CaseDetail

from .sources import Source

_MONTHS = (
    "stycznia",
    "lutego",
    "marca",
    "kwietnia",
    "maja",
    "czerwca",
    "lipca",
    "sierpnia",
    "września",
    "października",
    "listopada",
    "grudnia",
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])")
_WHITESPACE = re.compile(r"\s+")
_ARTICLE_PREFIX = re.compile(
    r"^(?:Art\.\s*\d+[a-z]?\.|§\s*\d+\.)\s*(?:\d+[a-z]?[.)]\s*)?"
)

_QUOTE_LIMIT = 200

_LEGAL_SENTENCES: dict[str, str] = {
    "udip#Art. 13.": (
        "Zgodnie z art. 13 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do "
        "informacji publicznej udostępnianie informacji publicznej na wniosek następuje "
        "bez zbędnej zwłoki, nie później niż w terminie 14 dni od dnia złożenia wniosku"
    ),
    "udip#Art. 10.": (
        "Informacja publiczna, która nie została udostępniona w Biuletynie Informacji "
        "Publicznej, jest udostępniana na wniosek"
    ),
    "udip#Art. 5.": (
        "Prawo do informacji publicznej podlega ograniczeniu ze względu na prywatność "
        "osoby fizycznej, przy czym ograniczenie nie dotyczy informacji o osobach "
        "pełniących funkcje publiczne"
    ),
    "zarzadzenie-412-2023#§ 4.": (
        "Zgodnie z § 4 zarządzenia nr 412/2023 Prezydenta Miasta Bydgoszczy komórka "
        "organizacyjna przygotowuje projekt odpowiedzi w terminie 7 dni roboczych od "
        "otrzymania wniosku"
    ),
}

_CLOSING_SENTENCE = (
    "Odmowa udostępnienia informacji publicznej następuje w drodze decyzji, do której "
    "stosuje się przepisy Kodeksu postępowania administracyjnego"
)

_LEGAL_ORDER: tuple[str, ...] = (
    "udip#Art. 13.",
    "udip#Art. 10.",
    "udip#Art. 5.",
    "zarzadzenie-412-2023#§ 4.",
)


def format_date_pl(value: date) -> str:
    """Data w formie urzędowej: „20 lutego 2026”."""
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year}"


def _as_single_sentence(text: str, limit: int = _QUOTE_LIMIT) -> str:
    """Skleja cytat w jedno zdanie, żeby odnośnik pokrywał całość wypowiedzi."""
    cleaned = _WHITESPACE.sub(" ", text).strip()
    parts = [part.strip() for part in _SENTENCE_END.split(cleaned) if part.strip()]
    joined = "; ".join(part.rstrip(".") for part in parts)
    if len(joined) > limit:
        joined = joined[:limit].rsplit(" ", 1)[0] + "…"
    return joined


def _by_id(sources: Sequence[Source]) -> dict[str, Source]:
    return {source.source_id: source for source in sources}


def _uploaded_statute_sentences(sources: Sequence[Source]) -> list[str]:
    """Wgrane ustawy i zarządzenia — cytat przepisu w podstawie prawnej.

    Przepisów z fixtures nie da się pomylić z wgranymi: te pierwsze mają
    `source_id` w postaci `udip#Art. 13.` i własne, gotowe zdania w
    `_LEGAL_SENTENCES`. Wgrany akt cytujemy dosłownie, bo szablon nie zna
    jego treści.
    """
    return [
        f"Podstawę prawną stanowi {source.label}: "
        f"{_as_single_sentence(_ARTICLE_PREFIX.sub('', source.text))} [^{source.ref}]."
        for source in sources
        if source.source_type == "statute" and source.source_id not in _LEGAL_SENTENCES
    ]


def _legal_paragraph(sources: Sequence[Source]) -> str:
    index = _by_id(sources)
    sentences = [
        f"{_LEGAL_SENTENCES[key]} [^{index[key].ref}]."
        for key in _LEGAL_ORDER
        if key in index and key in _LEGAL_SENTENCES
    ]
    sentences += _uploaded_statute_sentences(sources)
    if not sentences:
        return "Podstawa prawna zostanie uzupełniona."
    return " ".join(sentences)


def _closing_paragraph(sources: Sequence[Source]) -> str:
    index = _by_id(sources)
    source = index.get("udip#Art. 16.")
    if source is None:
        return "Projekt wymaga uzupełnienia o pouczenie."
    return f"{_CLOSING_SENTENCE} [^{source.ref}]."


def _archive_paragraphs(sources: Sequence[Source]) -> list[str]:
    return [
        f"W sprawie zbliżonej {source.label.split(' — ')[0]} organ zajął następujące "
        f"stanowisko: {_as_single_sentence(source.text)} [^{source.ref}]."
        for source in sources
        if source.source_type == "archive"
    ]


def _reply_paragraphs(sources: Sequence[Source]) -> list[str]:
    return [
        f"Komórka organizacyjna przekazała stanowisko: "
        f"{_as_single_sentence(source.text)} [^{source.ref}]."
        for source in sources
        if source.source_type == "department_reply"
    ]


def _document_paragraphs(sources: Sequence[Source]) -> list[str]:
    return [
        f"W aktach sprawy znajduje się dokument „{source.label}”: "
        f"{_as_single_sentence(source.text)} [^{source.ref}]."
        for source in sources
        if source.source_type == "document"
    ]


def build_template(case: CaseDetail, sources: Sequence[Source]) -> str:
    """Buduje treść projektu z szablonu — deterministycznie, bez modelu."""
    parts: list[str] = ["## Podstawa prawna", "", _legal_paragraph(sources), ""]

    parts += [
        "## Odpowiedź",
        "",
        "W odpowiedzi na wniosek o udostępnienie informacji publicznej z dnia "
        f"{format_date_pl(case.inflow_date)} r. dotyczący: {case.subject}, uprzejmie "
        "informuję, co następuje.",
        "",
    ]

    archive = _archive_paragraphs(sources)
    if archive:
        parts += ["## Rozstrzygnięcia w sprawach zbliżonych", "", *archive, ""]

    replies = _reply_paragraphs(sources)
    if replies:
        parts += ["## Stanowiska komórek organizacyjnych", "", *replies, ""]

    documents = _document_paragraphs(sources)
    if documents:
        parts += ["## Dokumenty w aktach sprawy", "", *documents, ""]

    parts += ["## Pouczenie", "", _closing_paragraph(sources), ""]

    if case.handler_initials:
        parts += [
            "Z upoważnienia Prezydenta Miasta Bydgoszczy",
            "",
            case.handler_initials,
        ]

    return "\n".join(parts).strip()
