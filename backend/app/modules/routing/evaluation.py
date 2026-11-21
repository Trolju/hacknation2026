"""Zbiór oceny routingu wydziałowego (WS4).

Ocena opiera się na ręcznie napisanym zbiorze `tests/data/cases.json`: dla
każdego z dziesięciu wniosków z `fixtures/cases/cases.json` zapisano komórki,
do których urzędnik naprawdę powinien wysłać zapytanie, wraz z uzasadnieniem
w polu `why`. Zbiór powstał z wiedzy o podziale zadań urzędu, a nie z wyniku
algorytmu — ale reguły dopasowania i zbiór powstały w tym samym module, więc
wynik jest górnym oszacowaniem, a nie niezależnym pomiarem.

Miary:

* **top-1** — pierwsza sugestia należy do zbioru oczekiwanego,
* **top-3** — wszystkie komórki oczekiwane mieszczą się w trzech pierwszych
  sugestiach (miara ostra: brak choćby jednej komórki to pomyłka).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "tests" / "data" / "cases.json"

#: Ranking zwraca identyfikatory komórek w kolejności od najlepszej sugestii.
Ranking = Callable[[str], list[str]]


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    case_number: str
    subject: str
    expected: tuple[str, ...]
    why: str


@dataclass(frozen=True)
class Accuracy:
    top1: float
    top3: float
    total: int
    misses: tuple[str, ...]


def load_eval_cases() -> list[EvalCase]:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return [
        EvalCase(
            case_id=row["case_id"],
            case_number=row["case_number"],
            subject=row["subject"],
            expected=tuple(row["expected"]),
            why=row["why"],
        )
        for row in raw
    ]


def evaluate(ranking: Ranking, cases: list[EvalCase] | None = None) -> Accuracy:
    """Liczba trafień top-1 i top-3 na zbiorze oceny."""
    samples = cases if cases is not None else load_eval_cases()
    if not samples:
        return Accuracy(top1=0.0, top3=0.0, total=0, misses=())

    top1_hits = 0
    top3_hits = 0
    misses: list[str] = []
    for sample in samples:
        ranked = ranking(sample.subject)
        if ranked and ranked[0] in sample.expected:
            top1_hits += 1
        else:
            misses.append(f"{sample.case_number}: top-1 = {ranked[:1] or 'brak'}")
        if set(sample.expected) <= set(ranked[:3]):
            top3_hits += 1
        else:
            misses.append(
                f"{sample.case_number}: top-3 = {ranked[:3] or 'brak'}, "
                f"oczekiwano {list(sample.expected)}"
            )

    total = len(samples)
    return Accuracy(
        top1=top1_hits / total,
        top3=top3_hits / total,
        total=total,
        misses=tuple(misses),
    )
