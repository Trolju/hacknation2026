"""Prompt dla modelu i kontrola pokrycia twierdzeń źródłami.

Dwie funkcje trzymają jakość projektu odpowiedzi:

1. `build_prompt` formułuje **twarde** wymaganie: każde zdanie merytoryczne
   musi nieść odnośnik `[^n]` do jednego ze źródeł. Model nie dostaje żadnej
   innej możliwości — nie wolno mu dopisywać faktów spoza listy źródeł.
2. `find_unsupported` sprawdza gotową treść niezależnie od modelu. Zdanie bez
   odnośnika (albo z odnośnikiem do nieistniejącego źródła) trafia do
   `unsupported` i jest pokazywane urzędnikowi. Nic nie jest usuwane po cichu.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence

from app.contracts import CaseDetail, DraftRequest

from .sources import Source

SYSTEM_PROMPT = (
    "Jesteś asystentem urzędnika Urzędu Miasta Bydgoszczy. Przygotowujesz projekt "
    "odpowiedzi na wniosek o udostępnienie informacji publicznej. Piszesz po polsku, "
    "stylem formalnym, bez emoji i bez żargonu technicznego. Wolno Ci używać wyłącznie "
    "faktów z dostarczonych źródeł — nie uzupełniasz brakujących danych domysłami."
)

MIN_USABLE_CHARS = 200
MIN_CLAIM_CHARS = 20
PROMPT_SOURCE_CHARS = 1200

_MARKER = re.compile(r"\[\^(\d+)\]")
_ONLY_MARKERS = re.compile(r"^(?:\[\^\d+\]\s*)+$")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])")
_LIST_PREFIX = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")

# Zdania czysto formalne — nie są twierdzeniami merytorycznymi, więc nie muszą
# mieć odnośnika. Wszystko inne bez odnośnika trafia do `unsupported`.
_FORMULAIC_PREFIXES: tuple[str, ...] = (
    "w odpowiedzi na wniosek",
    "uprzejmie informuję",
    "z poważaniem",
    "z upoważnienia",
    "niniejszym",
    "proszę o",
    "do wiadomości",
    "otrzymują",
    "sporządził",
    "podstawa prawna zostanie uzupełniona",
    "projekt wymaga uzupełnienia",
)


# ───────────────────────────────── prompt ──────────────────────────────────
def _source_block(source: Source) -> str:
    kind = {
        "statute": "przepis",
        "archive": "sprawa archiwalna",
        "document": "dokument sprawy",
        "department_reply": "odpowiedź komórki",
    }[source.source_type]
    text = source.text.strip()
    if len(text) > PROMPT_SOURCE_CHARS:
        text = text[:PROMPT_SOURCE_CHARS].rsplit(" ", 1)[0] + "…"
    return f"[{source.ref}] ({kind}) {source.label}\n{text}"


def build_prompt(case: CaseDetail, sources: Sequence[Source], req: DraftRequest) -> str:
    """Buduje prompt z sekcjami: sprawa, źródła, struktura, zasady."""
    tone = (
        "formalny, urzędowy"
        if req.tone == "formalny"
        else "formalny, ale uprzejmy — z zwrotami grzecznościowymi"
    )
    source_text = "\n\n".join(_source_block(source) for source in sources)
    if not source_text:
        source_text = "(brak źródeł — nie podawaj żadnych faktów)"

    return "\n".join(
        (
            "ZADANIE",
            "Przygotuj projekt odpowiedzi na wniosek o udostępnienie informacji publicznej.",
            "",
            "TWARDE WYMAGANIE — KAŻDE TWIERDZENIE MA ŹRÓDŁO",
            "Każde zdanie merytoryczne musi kończyć się odnośnikiem w formacie [^n],",
            "gdzie n to numer źródła z listy ŹRÓDŁA. Zdanie bez odnośnika zostanie",
            "oznaczone jako niepotwierdzone i pokazane urzędnikowi jako ostrzeżenie.",
            "Wolno używać wyłącznie numerów źródeł z listy. Nie dodawaj faktów, liczb,",
            "nazwisk ani dat, których nie ma w źródłach. Jeżeli źródła nie odpowiadają",
            "na pytanie z wniosku, napisz wprost, że informacja wymaga uzupełnienia.",
            "",
            "SPRAWA",
            f"- znak sprawy: {case.case_number}",
            f"- przedmiot wniosku: {case.subject}",
            f"- data wpływu: {case.inflow_date.isoformat()}",
            f"- termin odpowiedzi: {case.deadline.isoformat()}",
            f"- rodzaj wnioskodawcy: {case.applicant_type.value}",
            f"- osoba prowadząca: {case.handler_initials or 'nie wskazano'}",
            "",
            "ŹRÓDŁA",
            source_text,
            "",
            "WYMAGANA STRUKTURA (nagłówki poziomu drugiego)",
            "## Podstawa prawna",
            "## Odpowiedź",
            "## Rozstrzygnięcia w sprawach zbliżonych",
            "## Stanowiska komórek organizacyjnych",
            "## Pouczenie",
            "",
            "ZASADY",
            f"- ton wypowiedzi: {tone}",
            "- pisz pełnymi zdaniami, w trzeciej osobie, bez list punktowanych w treści",
            "- nie powtarzaj treści źródła dosłownie dłużej niż jedno zdanie",
            "- nie dodawaj podpisu ani danych kontaktowych, których nie ma w źródłach",
            "- zwróć wyłącznie treść projektu, bez komentarza i bez bloków kodu",
        )
    )


# ──────────────────────────── kontrola twierdzeń ───────────────────────────
def normalize_model_output(raw: str) -> str:
    """Czyści odpowiedź modelu: bloki kodu, zbędne spacje, puste linie."""
    text = _FENCE.sub("", raw.strip())
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def is_usable(body: str) -> bool:
    """Czy odpowiedź modelu nadaje się na projekt pisma.

    Model, który zwraca jedno zdanie albo sam komentarz, nie przygotował
    projektu. Taka treść nie może trafić do urzędnika jako gotowe pismo —
    wtedy wracamy do szablonu i mówimy o tym wprost w `unsupported`.
    """
    if len(body) < MIN_USABLE_CHARS:
        return False
    if not any(line.lstrip().startswith("#") for line in body.splitlines()):
        return False
    return bool(_MARKER.search(body))


def extract_refs(body: str) -> list[int]:
    """Numery odnośników użyte w treści, w kolejności pierwszego wystąpienia."""
    seen: list[int] = []
    for match in _MARKER.finditer(body):
        ref = int(match.group(1))
        if ref not in seen:
            seen.append(ref)
    return seen


def strip_invalid_refs(body: str, valid: Iterable[int]) -> str:
    """Usuwa odnośniki do źródeł, których nie ma na liście."""
    allowed = set(valid)

    def _replace(match: re.Match[str]) -> str:
        return match.group(0) if int(match.group(1)) in allowed else ""

    cleaned = _MARKER.sub(_replace, body)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return re.sub(r"\s+([.,;:!?])", r"\1", cleaned)


def _blocks(body: str) -> list[str]:
    """Akapity treści — model zawija wiersze, więc zdania łączymy w akapity."""
    blocks: list[str] = []
    current: list[str] = []

    def flush() -> None:
        if current:
            blocks.append(" ".join(current))
            current.clear()

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            flush()
            continue
        if _LIST_PREFIX.match(line):
            flush()
            blocks.append(_LIST_PREFIX.sub("", line))
            continue
        current.append(line)
    flush()
    return blocks


def _sentences(line: str) -> list[str]:
    parts = [part.strip() for part in _SENTENCE_END.split(line) if part.strip()]
    merged: list[str] = []
    for part in parts:
        if merged and _ONLY_MARKERS.fullmatch(part):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged


def _is_formulaic(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(lowered.startswith(prefix) for prefix in _FORMULAIC_PREFIXES)


def find_unsupported(body: str, valid: Iterable[int]) -> list[str]:
    """Zdania merytoryczne bez pokrycia w źródłach.

    Zdanie jest pokryte, gdy niesie odnośnik do istniejącego źródła. Zdania
    formalne (powitanie, podpis, formuła grzecznościowa) są dopuszczalne bez
    odnośnika — inaczej każde pismo miałoby kilkanaście fałszywych ostrzeżeń.
    """
    allowed = set(valid)
    found: list[str] = []
    for block in _blocks(body):
        for sentence in _sentences(block):
            if len(sentence) < MIN_CLAIM_CHARS:
                continue
            refs = [int(match.group(1)) for match in _MARKER.finditer(sentence)]
            if any(ref in allowed for ref in refs):
                continue
            if _is_formulaic(sentence):
                continue
            if sentence not in found:
                found.append(sentence)
    return found
