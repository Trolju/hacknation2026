"""Routing wydziałowy — dopasowanie po słowach kluczowych z wagami IDF (WS4).

Implementacja `app.ports.routing.DepartmentRouterPort`. Atrapa porównuje pierwsze
sześć znaków tokenu, więc gubi polską odmianę („dróg” vs „droga”) i traktuje
frazę tak samo jak pojedyncze słowo. Tutaj:

* **Rdzeniowanie** — odcinanie końcówek fleksyjnych bez bibliotek zewnętrznych.
  Token dostaje zbiór rdzeni (po jednym na każdą pasującą końcówkę), a dwa tokeny
  są zgodne, gdy ich zbiory się przecinają. Dzięki temu „wynagrodzenia”
  i „wynagrodzenie” trafiają w ten sam rdzeń, choć końcówki są różne, a „dróg”
  i „droga” spotykają się po sprowadzeniu znaków diakrytycznych do ASCII.
* **Frazy** — słowo kluczowe z kilku tokenów musi wystąpić w zapytaniu
  w tej samej kolejności i bez przerw. Fraza waży `PHRASE_WEIGHT` razy więcej
  niż pojedyncze słowo, bo jest bardziej swoista: „warunki zabudowy” to nie to
  samo co „warunki”.
* **IDF** — słowo kluczowe obecne w wielu komórkach waży mniej
  (`log(1 + N/df)`), więc „droga” (dwie komórki) nie przebije „wycinka”.
* **Kara za pokrycie** — komórka, której słowa kluczowe pokrywają tylko wycinek
  zapytania, dostaje mnożnik `0,5 + 0,5 * pokrycie`. Zapytanie o „koszty
  utrzymania Biura Rady Miasta” nie wskaże Wydziału Gospodarki Komunalnej tylko
  dlatego, że ma on frazę „utrzymanie miasta”.
* **Pewność** — `1 - exp(-wynik/2)` skalowane pozycją w rankingu. Funkcja jest
  ściśle rosnąca względem wyniku, więc kolejność pewności odpowiada kolejności
  trafności.

Zapytanie do komórek (`inquiry`) powstaje z rzeczywistych danych sprawy
pobranych przez `container.get_cases()` — numer, przedmiot, data wpływu, termin
i inicjały prowadzącego — a nie ze stałego szablonu.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from app.adapters.fakes import fixtures
from app.contracts import (
    ApplicantType,
    CaseDetail,
    Department,
    DepartmentSuggestion,
    GeneratedLetter,
    InquiryRequest,
    SuggestRequest,
)
from app.core.clock import today
from app.core.errors import NotFound, ValidationFailed

# ──────────────────────────────── stałe ─────────────────────────────────────
#: Mnożnik wagi dla słowa kluczowego złożonego z kilku tokenów.
PHRASE_WEIGHT = 2.0
#: Najkrótszy dopuszczalny rdzeń — krótsze fragmenty są zbyt wieloznaczne.
MIN_STEM = 3
#: Skala nasycenia pewności: `1 - exp(-wynik / CONFIDENCE_SCALE)`.
CONFIDENCE_SCALE = 2.0
#: Dolny mnożnik kary za pokrycie zapytania (komórka trafia w jedno słowo).
COVERAGE_FLOOR = 0.5
#: Zapas, o który komórka musi wyprzedzić ustawowy termin odpowiedzi.
INTERNAL_BUFFER_DAYS = 3
#: Górna granica `k` z kontraktu (`SuggestRequest.k`).
MAX_K = 10

LEGAL_BASIS = (
    "art. 9 ust. 1 oraz art. 13 ust. 1 ustawy z dnia 6 września 2001 r. "
    "o dostępie do informacji publicznej (Dz.U. z 2022 r. poz. 902 ze zm.)"
)

APPLICANT_LABEL: dict[ApplicantType, str] = {
    ApplicantType.OSOBA_FIZYCZNA: "osoba fizyczna",
    ApplicantType.ORGANIZACJA: "organizacja",
    ApplicantType.MEDIA: "media",
    ApplicantType.INNE: "inny podmiot",
}

# ────────────────────────── normalizacja tekstu ─────────────────────────────
_FOLD = str.maketrans(
    {
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ź": "z",
        "ż": "z",
    }
)
_TOKEN = re.compile(r"[a-z]+")

#: Końcówki fleksyjne polskich rzeczowników, przymiotników i imiesłowów.
_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "owaniami",
            "eniami",
            "aniami",
            "owania",
            "eniu",
            "enia",
            "enie",
            "ania",
            "anie",
            "ami",
            "ach",
            "ymi",
            "imi",
            "ych",
            "ich",
            "iej",
            "ego",
            "emu",
            "owi",
            "ow",
            "om",
            "em",
            "ie",
            "iu",
            "ia",
            "ej",
            "ym",
            "im",
            "a",
            "e",
            "i",
            "o",
            "u",
            "y",
        },
        key=lambda suffix: (-len(suffix), suffix),
    )
)

#: Słowa funkcyjne i bojlerypowe zwroty UDIP — nie niosą informacji o komórce.
#: „informacja publiczna” i „wniosek UDIP” występują w niemal każdym wniosku,
#: więc po odfiltrowaniu tych tokenów nie wskazują żadnej komórki.
_STOPWORDS = frozenset(
    (
        "a", "aby", "albo", "ale", "az", "bez", "bo", "by", "byc", "byl", "byla",
        "bylo", "byly", "bym", "bys", "czy", "dla", "do", "gdy", "gdzie", "go",
        "i", "ich", "ile", "im", "inne", "jak", "jako", "je", "jego", "jej",
        "jest", "jestem", "jesli", "juz", "kiedy", "kto", "ktora", "ktore",
        "ktorego", "ktorej", "ktory", "ktorych", "ktorym", "lat", "lub", "ma",
        "mi", "mnie", "moze", "na", "nad", "nam", "nas", "nie", "niego", "niej",
        "nim", "niz", "o", "od", "oraz", "po", "pod", "ponad", "przed", "przez",
        "przy", "raz", "rok", "roku", "sa", "sie", "sobie", "sposob", "swoje",
        "ta", "tak", "takze", "te", "tego", "tej", "ten", "teraz", "tez", "to",
        "tych", "tylko", "tym", "u", "w", "we", "wiec", "z", "za", "ze", "zeby",
        "jeszcze", "bardzo",
        # formuły UDIP — występują w niemal każdym wniosku
        "prosze", "prosba", "zwiazku", "dotyczy", "dotyczacy", "dotyczace",
        "dotyczacych", "udostepnienie", "udostepnienia", "udostepnic",
        "informacja", "informacji", "informacje", "publiczna", "publicznej",
        "publicznych", "wniosek", "wniosku", "wnioskodawca", "udip",
        "dane", "danych", "dana",
        # jednostki czasu
        "dzien", "dnia", "dni",
    )
)


def _stems(token: str) -> frozenset[str]:
    """Zbiór rdzeni tokenu — pełna postać plus każda pasująca końcówka odcięta."""
    variants = {token}
    # „e” ruchome: najem → najm, węgiel → węgl.
    if len(token) >= 4 and token[-2] == "e" and token[-1] not in "aeiouy":
        variants.add(token[:-2] + token[-1])
    stems: set[str] = set()
    for variant in variants:
        stems.add(variant)
        for suffix in _SUFFIXES:
            if variant.endswith(suffix) and len(variant) - len(suffix) >= MIN_STEM:
                stems.add(variant[: -len(suffix)])
    return frozenset(stems)


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower().translate(_FOLD))


def _content_tokens(text: str) -> list[str]:
    """Tokeny istotne dla routingu — bez słów funkcyjnych i krótkich resztek."""
    return [token for token in _tokens(text) if len(token) >= MIN_STEM and token not in _STOPWORDS]


# ───────────────────────────── model słowa kluczowego ───────────────────────
@dataclass(frozen=True)
class Keyword:
    """Słowo kluczowe komórki w postaci gotowej do dopasowania."""

    text: str
    stems: tuple[frozenset[str], ...]
    idf: float

    @property
    def is_phrase(self) -> bool:
        return len(self.stems) > 1

    @property
    def weight(self) -> float:
        return self.idf * (PHRASE_WEIGHT if self.is_phrase else 1.0)


@dataclass(frozen=True)
class ScoredDepartment:
    """Komórka z wynikiem trafności — wewnętrzny format rankingu."""

    department_id: str
    name: str
    raw: float
    confidence: float
    rationale: str
    matched_terms: tuple[str, ...]


def _build_keywords(rows: list[dict[str, Any]]) -> dict[str, list[Keyword]]:
    """Słowa kluczowe per komórka, z IDF liczonym po całej taksonomii."""
    total = len(rows)
    prepared: dict[str, list[tuple[str, tuple[str, ...], tuple[frozenset[str], ...]]]] = {}
    frequency: dict[tuple[str, ...], int] = {}
    for row in rows:
        entries: list[tuple[str, tuple[str, ...], tuple[frozenset[str], ...]]] = []
        for raw in row["keywords"]:
            tokens = tuple(_content_tokens(raw))
            if not tokens:
                continue
            frequency[tokens] = frequency.get(tokens, 0) + 1
            entries.append((raw, tokens, tuple(_stems(token) for token in tokens)))
        prepared[row["id"]] = entries

    return {
        department_id: [
            Keyword(
                text=raw,
                stems=stems,
                idf=math.log(1.0 + total / frequency[tokens]),
            )
            for raw, tokens, stems in entries
        ]
        for department_id, entries in prepared.items()
    }


def _locate(keyword: Keyword, query: list[frozenset[str]]) -> list[int] | None:
    """Indeksy tokenów zapytania pokrytych przez słowo kluczowe (albo `None`)."""
    size = len(keyword.stems)
    for start in range(len(query) - size + 1):
        if all(query[start + offset] & keyword.stems[offset] for offset in range(size)):
            return list(range(start, start + size))
    return None


def _rationale(matches: list[tuple[Keyword, list[int]]], covered: int, total: int) -> str:
    phrases = [keyword.text for keyword, _ in matches if keyword.is_phrase]
    words = [keyword.text for keyword, _ in matches if not keyword.is_phrase]
    parts: list[str] = []
    if phrases:
        parts.append("fraza " + ", ".join(f"„{text}”" for text in phrases))
    if words:
        parts.append("słowo " + ", ".join(f"„{text}”" for text in words))
    head = "Dopasowane słowa kluczowe: " + ", ".join(parts)
    return f"{head}. Pokrycie zapytania: {covered} z {total} istotnych słów."


def rank_departments(text: str, rows: list[dict[str, Any]]) -> list[ScoredDepartment]:
    """Ranking komórek dla zapytania — pełna lista, posortowana malejąco.

    Wydzielone z klasy, żeby dało się sprawdzić monotoniczność pewności
    względem wyniku bez sięgania do prywatnego stanu adaptera.
    """
    query = [_stems(token) for token in _content_tokens(text)]
    if not query:
        return []

    keywords = _build_keywords(rows)
    candidates: list[tuple[float, dict[str, Any], list[tuple[Keyword, list[int]]], int]] = []
    for row in rows:
        matches: list[tuple[Keyword, list[int]]] = []
        covered: set[int] = set()
        for keyword in keywords[row["id"]]:
            hit = _locate(keyword, query)
            if hit is None:
                continue
            matches.append((keyword, hit))
            covered.update(hit)
        if not matches:
            continue
        factor = COVERAGE_FLOOR + (1.0 - COVERAGE_FLOOR) * (len(covered) / len(query))
        raw = sum(keyword.weight for keyword, _ in matches) * factor
        candidates.append((raw, row, matches, len(covered)))

    if not candidates:
        return []

    candidates.sort(key=lambda item: (-item[0], item[1]["id"]))
    strongest = candidates[0][0]
    scored: list[ScoredDepartment] = []
    for raw, row, matches, covered_count in candidates:
        strength = 1.0 - math.exp(-raw / CONFIDENCE_SCALE)
        share = raw / strongest if strongest > 0 else 0.0
        confidence = min(max(strength * (0.55 + 0.45 * share), 0.0), 1.0)
        scored.append(
            ScoredDepartment(
                department_id=row["id"],
                name=row["name"],
                raw=raw,
                confidence=round(confidence, 4),
                rationale=_rationale(matches, covered_count, len(query)),
                matched_terms=tuple(keyword.text for keyword, _ in matches),
            )
        )
    return scored


# ──────────────────────────────── zapytanie ─────────────────────────────────
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


def _pl_date(value: date) -> str:
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year} r."


def build_inquiry_body(case: CaseDetail, names: list[str], *, reference: date) -> str:
    """Treść zapytania złożona z danych sprawy — bez stałego szablonu."""
    internal = case.deadline - timedelta(days=INTERNAL_BUFFER_DAYS)
    if internal < reference:
        internal = reference
    span = (case.deadline - case.inflow_date).days

    paragraphs: list[str] = [
        f"Bydgoszcz, {_pl_date(reference)}",
        "",
        f"Znak sprawy: {case.case_number}",
        f"Data wpływu wniosku: {_pl_date(case.inflow_date)}",
        f"Termin odpowiedzi: {_pl_date(case.deadline)}",
        f"Typ wnioskodawcy: {APPLICANT_LABEL[case.applicant_type]}",
        "",
        "Adresaci:",
        "\n".join(f"{index}. {name}" for index, name in enumerate(names, start=1)),
        "",
        f"Dotyczy: {case.subject}",
        "",
        "Szanowni Państwo,",
        "",
        "zwracam się z prośbą o przygotowanie materiałów niezbędnych do udzielenia "
        f"odpowiedzi na wniosek o udostępnienie informacji publicznej znak "
        f"{case.case_number} z dnia {_pl_date(case.inflow_date)}, dotyczący: "
        f"„{case.subject}”.",
        "",
        f"Materiały proszę przekazać do {_pl_date(internal)} Ustawowy termin "
        f"odpowiedzi upływa {_pl_date(case.deadline)}, tj. {span} dni od dnia wpływu "
        "wniosku.",
    ]
    if case.deadline < reference:
        paragraphs.extend(
            [
                "",
                f"Uwaga: ustawowy termin odpowiedzi upłynął {_pl_date(case.deadline)} — "
                "materiały są potrzebne niezwłocznie.",
            ]
        )
    paragraphs.extend(
        [
            "",
            f"Podstawa prawna: {LEGAL_BASIS}.",
            "",
            "Jeżeli przekazanie materiałów w tym terminie nie jest możliwe, proszę "
            "o niezwłoczne wskazanie przewidywanego terminu i przyczyn opóźnienia — "
            "zgodnie z art. 13 ust. 2 ustawy przedłużenie terminu wymaga zawiadomienia "
            "wnioskodawcy przed upływem terminu ustawowego.",
        ]
    )
    if case.handler_initials:
        paragraphs.extend(["", f"Sprawę prowadzi: {case.handler_initials}."])
    paragraphs.extend(
        [
            "",
            "Z poważaniem",
            "Koordynator ds. dostępu do informacji publicznej",
            "Urząd Miasta Bydgoszczy",
        ]
    )
    return "\n".join(paragraphs)


# ──────────────────────────────── adapter ───────────────────────────────────
class KeywordDepartmentRouter:
    """Routing po słowach kluczowych z wagami IDF i dopasowaniem fraz."""

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = fixtures.departments()
        self._by_id: dict[str, dict[str, Any]] = {row["id"]: row for row in self._rows}

    def departments(self) -> list[Department]:
        return [Department(**row) for row in self._rows]

    def suggest(self, req: SuggestRequest) -> list[DepartmentSuggestion]:
        limit = max(1, min(req.k, MAX_K))
        return [
            DepartmentSuggestion(
                department_id=scored.department_id,
                name=scored.name,
                confidence=scored.confidence,
                rationale=scored.rationale,
                matched_terms=list(scored.matched_terms),
            )
            for scored in rank_departments(req.text, self._rows)[:limit]
        ]

    def inquiry(self, req: InquiryRequest) -> GeneratedLetter:
        # Import lokalny: kontener sam importuje ten moduł, więc zależność
        # w drugą stronę trzymamy poza czasem ładowania.
        from app.core import container

        names: list[str] = []
        for department_id in req.department_ids:
            row = self._by_id.get(department_id)
            if row is None:
                raise NotFound(
                    f"Nie znaleziono komórki o identyfikatorze {department_id}.",
                    details={"department_id": department_id},
                )
            names.append(row["name"])
        if not names:
            raise ValidationFailed("Wskaż co najmniej jedną komórkę organizacyjną.")

        case = container.get_cases().get(req.case_id)
        return GeneratedLetter(
            title=f"Zapytanie do komórek organizacyjnych — {case.case_number}",
            body=build_inquiry_body(case, names, reference=today()),
            addressees=names,
        )
