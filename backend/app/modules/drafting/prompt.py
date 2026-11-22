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
from .text import MONTHS, split_sentences

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
_LIST_PREFIX = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")

#: Model pisze odnośniki jako `[1]`, a nie `[^1]`. Bez normalizacji `is_usable`
#: nie znajduje ani jednego odnośnika i odrzuca poprawną, kompletną treść —
#: w pomiarach 4 z 20 generacji (20%) schodziło przez to do szablonu.
#: Wyjątki: `[^1]` (już poprawny) i `[1](url)` (link markdown).
_PLAIN_REF = re.compile(r"(?<!\^)\[(\d{1,2})\](?!\()")

#: Definicje przypisów (`[^1]: art. 13 …`) to warsztat modelu, nie treść pisma.
#: Zostawione na końcu trafiały do eksportu DOCX i PDF jako zwykły akapit.
_FOOTNOTE_DEF = re.compile(r"^[ \t]*\[\^\d+\]:.*$", re.MULTILINE)

#: Pismo urzędowe nie zawiera daty w formacie ISO. Model sporadycznie wstawiał
#: `2026-03-02` zamiast „2 marca 2026 r." — w pomiarach jeden projekt na dziesięć.
#: Skrót „r." po dacie i kropka kończąca zdanie są pochłaniane, bo „r." samo
#: kończy się kropką — inaczej wychodziło „…2026 r..".
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b(?:\s*r\.)?\.?")

#: Ciąg odnośników pod rząd to w wydruku kilkanaście cyfr w indeksie górnym
#: przy jednym zdaniu. Przebiegi trzech i więcej zwężamy do zakresu
#: `[^2]–[^13]`; `extract_refs` rozwija zakres, więc cytowania zostają pełne.
_REF_RUN = re.compile(r"(?:\[\^\d+\]){3,}")
_REF_TOKEN = re.compile(r"\[\^(\d+)\]–\[\^(\d+)\]|\[\^(\d+)\]")

# Zdania czysto formalne — nie są twierdzeniami merytorycznymi, więc nie muszą
# mieć odnośnika. Wszystko inne bez odnośnika trafia do `unsupported`.
_FORMULAIC_PREFIXES: tuple[str, ...] = (
    "w odpowiedzi na wniosek",
    "uprzejmie informuję",
    "z poważaniem",
    "z wyrazami szacunku",
    "łączę wyrazy szacunku",
    "z upoważnienia",
    "niniejszym",
    "proszę o",
    "do wiadomości",
    "otrzymują",
    "sporządził",
    "biuro komunikacji społecznej",
    "urząd miasta bydgoszczy",
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
            f"- wnioskodawca: {case.applicant or 'nie ustalono'}",
            f"- data wpływu: {case.inflow_date.isoformat()}",
            f"- termin odpowiedzi: {case.deadline.isoformat()}",
            f"- rodzaj wnioskodawcy: {case.applicant_type.value}",
            f"- osoba prowadząca: {case.handler_initials or 'nie wskazano'}",
            "",
            "PROCEDURA URZĘDOWA (Zarządzenie Prezydenta Miasta Bydgoszczy Nr 536/2024)",
            "- Administrator Informacji Publicznej (AIP) rejestruje wniosek i koordynuje",
            "  odpowiedź; projekt przygotowuje Wydział merytoryczny (§ 9–§ 11 ust. 1).",
            "- Gdy Wydział nie jest w posiadaniu informacji, pismo wskazuje jednostkę",
            "  właściwą w zakresie wnioskowanych danych (§ 11 ust. 3).",
            "- Gdy dokumentacja jest w archiwum zakładowym, właściwy jest Wydział, który",
            "  przekazał tam sprawę (§ 11 ust. 4).",
            "- Gdy informacja jest przetworzona, odpowiedź zawiera uzasadnienie takiego",
            "  stanowiska (§ 11 ust. 7).",
            "- Gdy informacja jest chroniona prawem, zamiast odpowiedzi powstaje projekt",
            "  decyzji administracyjnej o odmowie (§ 11 ust. 9).",
            "- Dane osobowe anonimizuje się przed przekazaniem informacji (§ 11 ust. 8).",
            "- Odpowiedź podpisuje Biuro Komunikacji Społecznej; wysyła ją urzędnik,",
            "  nigdy system automatycznie.",
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
            "## Podpis",
            "",
            "PISMO URZĘDOWE",
            "- sekcję „## Odpowiedź” otwiera zwrot grzecznościowy w osobnej linii:",
            "  „Szanowny Panie,” dla mężczyzny, „Szanowna Pani,” dla kobiety,",
            "  „Szanowni Państwo,” dla organizacji, mediów i wnioskodawcy nieustalonego;",
            "- sekcja „## Podpis” zawiera w osobnych liniach: „Łączę wyrazy szacunku,”,",
            "  „Biuro Komunikacji Społecznej” oraz „Urząd Miasta Bydgoszczy”;",
            "- nie dodawaj adresu, telefonu ani adresu e-mail urzędu — dokłada je eksport.",
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
def _polish_date(match: re.Match[str]) -> str:
    """Data ISO na zapis urzędowy; nieczytelna data zostaje bez zmian."""
    year, month, day = (int(match.group(index)) for index in (1, 2, 3))
    if not 1 <= month <= 12 or not 1 <= day <= 31:
        return match.group(0)
    return f"{day} {MONTHS[month - 1]} {year} r."


def normalize_model_output(raw: str) -> str:
    """Czyści odpowiedź modelu: bloki kodu, odnośniki, przypisy, daty.

    Kolejność ma znaczenie: najpierw ujednolicamy odnośniki, żeby definicje
    zapisane jako `[1]: …` też stały się `[^1]: …` i zostały usunięte.
    """
    text = _FENCE.sub("", raw.strip())
    text = _PLAIN_REF.sub(r"[^\1]", text)
    text = _FOOTNOTE_DEF.sub("", text)
    text = _ISO_DATE.sub(_polish_date, text)
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def _collapse_segment(refs: list[int]) -> str:
    """Kolejne numery zwęża do zakresu, krótsze zostawia wypisane."""
    if len(refs) >= 3:
        return f"[^{refs[0]}]–[^{refs[-1]}]"
    return "".join(f"[^{ref}]" for ref in refs)


def collapse_ref_runs(body: str) -> str:
    """Zwęża przebiegi trzech i więcej kolejnych odnośników do zakresu.

    Model powołuje się jednym zdaniem na wszystkie artykuły wgranej ustawy.
    Dwanaście cyfr w indeksie górnym przy jednym zdaniu jest nieczytelne
    w wydruku, więc `[^2][^3][^4][^5]` staje się `[^2]–[^5]`.

    Przebieg bywa nieściśle kolejny — `[^2]…[^12][^16]` — więc zwężamy każdy
    jego ciągły fragment osobno. Numer, który wypada z kolejności, zostaje
    wypisany, bo zakres obejmujący lukę kłamałby o treści.
    """

    def _replace(match: re.Match[str]) -> str:
        refs = [int(found.group(1)) for found in _MARKER.finditer(match.group(0))]
        parts: list[str] = []
        start = 0
        for index in range(1, len(refs) + 1):
            if index == len(refs) or refs[index] != refs[index - 1] + 1:
                parts.append(_collapse_segment(refs[start:index]))
                start = index
        return "".join(parts)

    return _REF_RUN.sub(_replace, body)


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
    """Numery odnośników użyte w treści, w kolejności pierwszego wystąpienia.

    Zakres `[^2]–[^13]` rozwija się do wszystkich numerów — inaczej po
    zwężeniu przebiegu cytowania gubiłyby źródła ze środka zakresu.
    """
    seen: list[int] = []
    for match in _REF_TOKEN.finditer(body):
        if match.group(1) is not None:
            refs: Iterable[int] = range(int(match.group(1)), int(match.group(2)) + 1)
        else:
            refs = (int(match.group(3)),)
        for ref in refs:
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
    merged: list[str] = []
    for part in split_sentences(line):
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
