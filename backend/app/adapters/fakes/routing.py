"""Atrapa routingu wydziałowego — dopasowanie słów kluczowych."""

from __future__ import annotations

import math
import re
from datetime import date

from app.adapters.fakes import fixtures
from app.contracts import (
    Department,
    DepartmentSuggestion,
    GeneratedLetter,
    InquiryRequest,
    SuggestRequest,
)
from app.core.clock import today
from app.core.errors import NotFound, ValidationFailed

_WORD = re.compile(r"[a-ząćęłńóśźż]{4,}")
_STEM = 6
_FOLD = str.maketrans("ąćęłńóśźż", "acelnoszz")
_VOWELS = "aeiouy"

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
    """Data w formie urzędowej: „6 marca 2026 r.”."""
    return f"{value.day} {_MONTHS[value.month - 1]} {value.year} r."


def _stem(token: str) -> str:
    """Rdzeń tokenu: bez znaków diakrytycznych, 6 znaków, bez końcowej samogłoski.

    Prosty zabieg wystarcza, żeby „droga” i „dróg” albo „rada” i „rady”
    trafiły w to samo słowo kluczowe.
    """
    folded = token.translate(_FOLD)[:_STEM]
    return folded.rstrip(_VOWELS) or folded


def _norm(text: str) -> set[str]:
    """Zbiór rdzeni — odporny na odmianę i pisownię z ogonkami."""
    return {_stem(token) for token in _WORD.findall(text.lower())}


def _keyword_weight(keyword: str, rows: list[dict]) -> float:
    """Waga słowa kluczowego — im rzadsze w taksonomii, tym większa (IDF).

    Bez tego ogólne słowa („miasta”, „urzędu”) wygrywały z konkretnymi
    („wynagrodzenie”), bo trafiały w wiele komórek naraz.
    """
    stems = _norm(keyword)
    owners = sum(1 for row in rows if any(_norm(k) & stems for k in row["keywords"]))
    return math.log(1 + len(rows) / max(owners, 1))


class FakeDepartmentRouter:
    def __init__(self) -> None:
        self._rows = fixtures.departments()
        self._by_id = {r["id"]: r for r in self._rows}
        self._weights = {
            keyword: _keyword_weight(keyword, self._rows)
            for row in self._rows
            for keyword in row["keywords"]
        }

    def departments(self) -> list[Department]:
        return [Department(**r) for r in self._rows]

    def _match(self, keyword: str, words: set[str]) -> float:
        """Trafienie słowa kluczowego: waga IDF razy pokrycie jego słów.

        Fraza wielowyrazowa trafiona jednym słowem („budynek urzędu” przy
        zapytaniu o „urząd”) liczy się tylko częściowo.
        """
        stems = _norm(keyword)
        if not stems:
            return 0.0
        covered = len(stems & words) / len(stems)
        return self._weights.get(keyword, 0.0) * covered

    def suggest(self, req: SuggestRequest) -> list[DepartmentSuggestion]:
        words = _norm(req.text)
        scored: list[tuple[float, dict, list[str]]] = []
        for row in self._rows:
            hits = [(k, self._match(k, words)) for k in row["keywords"]]
            matched = [(k, weight) for k, weight in hits if weight > 0.0]
            if not matched:
                continue
            raw = sum(weight for _, weight in matched)
            scored.append((raw, row, [k for k, _ in matched]))
        scored.sort(key=lambda x: -x[0])
        if not scored:
            return []
        top = scored[0][0] or 1.0
        out: list[DepartmentSuggestion] = []
        for score, row, terms in scored[: req.k]:
            out.append(
                DepartmentSuggestion(
                    department_id=row["id"],
                    name=row["name"],
                    confidence=round(min(score / top, 1.0) * 0.95, 3),
                    rationale="Dopasowanie po słowach: " + ", ".join(terms[:4]),
                    matched_terms=terms[:6],
                )
            )
        return out

    def inquiry(self, req: InquiryRequest) -> GeneratedLetter:
        names = []
        for did in req.department_ids:
            row = self._by_id.get(did)
            if row is None:
                raise NotFound(f"Nie znaleziono komórki o identyfikatorze {did}.")
            names.append(row["name"])
        if not names:
            raise ValidationFailed("Wskaż co najmniej jedną komórkę organizacyjną.")

        # Import lokalny: kontener sam importuje ten moduł, więc zależność
        # w drugą stronę trzymamy poza czasem ładowania.
        from app.core import container

        case = container.get_cases().get(req.case_id)
        body = "\n".join(
            [
                f"Bydgoszcz, {_pl_date(today())}",
                "",
                f"Znak sprawy: {case.case_number}",
                f"Data wpływu wniosku: {_pl_date(case.inflow_date)}",
                f"Termin odpowiedzi: {_pl_date(case.deadline)}",
                "",
                "Adresaci:",
                "\n".join(f"{index}. {name}" for index, name in enumerate(names, start=1)),
                "",
                f"Dotyczy: {case.subject}",
                "",
                "Szanowni Państwo,",
                "",
                "w związku z wnioskiem o udostępnienie informacji publicznej proszę "
                "o przygotowanie materiałów niezbędnych do udzielenia odpowiedzi "
                "w zakresie opisanym w wniosku.",
                "",
                "Proszę o przekazanie odpowiedzi w terminie 7 dni roboczych od otrzymania "
                "niniejszego zapytania. W przypadku konieczności przeprowadzenia kwerendy "
                "proszę o wskazanie przewidywanego terminu.",
                "",
                "Z poważaniem",
                "Koordynator ds. dostępu do informacji publicznej",
            ]
        )
        return GeneratedLetter(
            title=f"Zapytanie do komórek organizacyjnych — {case.case_number}",
            body=body,
            addressees=names,
        )
