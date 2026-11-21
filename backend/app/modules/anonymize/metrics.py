"""Zbiór oceny i metryki anonimizacji (WS6).

`fixtures/anonymization/labeled.jsonl` jest zbiorem dymnym — reguły atrapy były
do niego dostrajane, więc osiąga na nim 1.0 i nie mierzy jakości. Właściwą
miarą jest ręcznie napisany zbiór `heldout.jsonl` w katalogu testów modułu:
inne nazwiska, ulice, miasta i konstrukcje zdaniowe.

Metryki liczone są jak w atrapie: dopasowanie dokładne po trójce
`(start, end, category)`. Kategoria musi się zgadzać — inaczej span jest
liczony jako błąd, bo urzędnik zobaczyłby złe oznaczenie.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from app.contracts import AnonymizerMetrics, CategoryMetrics, DetectRequest, Span

HELDOUT_PATH = Path(__file__).resolve().parent / "tests" / "data" / "heldout.jsonl"

Sample = dict[str, Any]
DetectFn = Callable[[DetectRequest], list[Span]]


def load_heldout(path: Path | None = None) -> list[Sample]:
    """Wczytuje zbiór held-out (JSONL: `id`, `text`, `spans`)."""
    source = path or HELDOUT_PATH
    lines = source.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def gold_keys(sample: Sample) -> set[tuple[int, int, str]]:
    return {(int(s["start"]), int(s["end"]), str(s["category"])) for s in sample["spans"]}


def predicted_keys(spans: Iterable[Span]) -> set[tuple[int, int, str]]:
    return {(s.start, s.end, s.category.value) for s in spans}


def evaluate_samples(samples: Sequence[Sample], detect: DetectFn) -> AnonymizerMetrics:
    """Precyzja, pełność i F1 na parach (zbiór, detektor)."""
    tp = fp = fn = 0
    per: dict[str, list[int]] = {}
    for sample in samples:
        gold = gold_keys(sample)
        pred = predicted_keys(detect(DetectRequest(text=sample["text"])))
        for key in gold & pred:
            tp += 1
            per.setdefault(key[2], [0, 0, 0])[0] += 1
        for key in pred - gold:
            fp += 1
            per.setdefault(key[2], [0, 0, 0])[1] += 1
        for key in gold - pred:
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
            category: CategoryMetrics(
                precision=round(v[0] / (v[0] + v[1]), 4) if v[0] + v[1] else 0.0,
                recall=round(v[0] / (v[0] + v[2]), 4) if v[0] + v[2] else 0.0,
                support=v[0] + v[2],
            )
            for category, v in sorted(per.items())
        },
    )


def error_report(samples: Sequence[Sample], detect: DetectFn) -> list[str]:
    """Czytelna lista pomyłek — używana w testach i przy strojeniu reguł."""
    problems: list[str] = []
    for sample in samples:
        gold = gold_keys(sample)
        pred = predicted_keys(detect(DetectRequest(text=sample["text"])))
        for start, end, category in sorted(pred - gold):
            problems.append(
                f"{sample['id']}: nadmiar {category} {sample['text'][start:end]!r} "
                f"({start}-{end})"
            )
        for start, end, category in sorted(gold - pred):
            problems.append(
                f"{sample['id']}: brak {category} {sample['text'][start:end]!r} "
                f"({start}-{end})"
            )
    return problems
