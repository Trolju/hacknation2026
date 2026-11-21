"""Atrapa wyszukiwania archiwalnego — TF-IDF na fixtures.

Baseline: tokenizacja + waga IDF + cosinus. Implementacja produkcyjna (WS3)
dodaje wektory i rerank, ale musi pobić ten baseline na jakości.

Atrapa trzyma archiwum w pamięci procesu. `add` dopisuje sprawę i przebudowuje
indeks, więc zamknięcie wniosku jest widoczne w wyszukiwaniu do restartu —
trwałość zapewnia dopiero adapter realny.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from app.adapters.fakes import fixtures
from app.contracts import ArchiveCase, SimilarCase, SimilarRequest
from app.core.errors import NotFound

_WORD = re.compile(r"[a-ząćęłńóśźż]{4,}")
_STOP = frozenset(
    (
        "oraz", "przez", "dla", "tego", "który", "która", "które", "zostać", "został",
        "zostały", "jest", "są", "nie", "tak", "przy", "pod", "nad", "jak", "ich", "jego",
        "jej", "tym", "te", "ta", "ten", "być", "może", "można", "także", "również",
        "informacji", "publicznej", "wniosek", "wnoszę", "proszę", "udostępnienie", "zwracam",
        "się",
    )
)


def _tokens(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in _STOP]


class FakeArchiveSearch:
    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {
            r["archive_id"]: dict(r) for r in fixtures.archive()
        }
        self._docs: dict[str, Counter[str]] = {}
        self._idf: dict[str, float] = {}
        self._rebuild()

    def _rebuild(self) -> None:
        """Przelicza wektory i IDF od zera — po każdym `add`."""
        self._docs = {
            aid: Counter(_tokens(r["request_text"] + " " + r["subject"]))
            for aid, r in self._rows.items()
        }
        df: Counter[str] = Counter()
        for counts in self._docs.values():
            df.update(counts.keys())
        n = max(len(self._docs), 1)
        self._idf = {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    def _vec(self, counts: Counter[str]) -> dict[str, float]:
        return {t: c * self._idf.get(t, 1.0) for t, c in counts.items()}

    def _next_id(self) -> str:
        """Kolejny identyfikator dla spraw dopisanych w tej sesji.

        Fixtures zajmują `a0001`–`a0049`; nowe sprawy dostają prefiks `n`, żeby
        nigdy nie kolidowały z numeracją archiwum dostarczonego w materiałach.
        """
        used = {
            int(aid[1:])
            for aid in self._rows
            if aid.startswith("n") and aid[1:].isdigit()
        }
        return f"n{max(used, default=0) + 1:04d}"

    def similar(self, req: SimilarRequest) -> list[SimilarCase]:
        q = self._vec(Counter(_tokens(req.text)))
        qn = math.sqrt(sum(v * v for v in q.values())) or 1.0
        scored: list[tuple[float, str, list[str]]] = []
        for aid, counts in self._docs.items():
            row = self._rows[aid]
            if req.year_from is not None and row["year"] < req.year_from:
                continue
            d = self._vec(counts)
            dn = math.sqrt(sum(v * v for v in d.values())) or 1.0
            dot = sum(q.get(t, 0.0) * v for t, v in d.items())
            score = dot / (qn * dn)
            if score <= 0:
                continue
            shared = sorted(
                (t for t in q if t in d), key=lambda t: -q[t] * d[t]
            )[:6]
            scored.append((score, aid, shared))
        scored.sort(key=lambda x: -x[0])
        out: list[SimilarCase] = []
        for score, aid, shared in scored[: req.k]:
            row = self._rows[aid]
            out.append(
                SimilarCase(
                    archive_id=aid,
                    case_number=row["case_number"],
                    subject=row["subject"],
                    year=row["year"],
                    score=round(min(score, 1.0), 4),
                    snippet=row["request_text"][:220].strip(),
                    matched_terms=shared,
                    response_excerpt=row["response_text"][:220].strip(),
                )
            )
        return out

    def get(self, archive_id: str) -> ArchiveCase:
        row = self._rows.get(archive_id)
        if row is None:
            raise NotFound("Nie znaleziono sprawy archiwalnej.")
        return ArchiveCase(**row)

    def size(self) -> int:
        return len(self._rows)

    def add(self, case: ArchiveCase) -> str:
        for aid, row in self._rows.items():
            if row["case_number"] == case.case_number:
                return aid
        archive_id = case.archive_id or self._next_id()
        self._rows[archive_id] = {
            "archive_id": archive_id,
            "case_number": case.case_number,
            "subject": case.subject,
            "year": case.year,
            "request_text": case.request_text,
            "response_text": case.response_text,
            "departments": list(case.departments),
        }
        self._rebuild()
        return archive_id
