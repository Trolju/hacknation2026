"""Realny adapter wyszukiwania archiwalnego (WS3).

Implementacja `app.ports.archive.ArchiveSearchPort`. Wyszukiwanie jest
hybrydowe — trzy sygnały, scalane w jedną ocenę:

1. **Leksykalny** — BM25 po temacie i treści wniosku. Czysty Python, bez
   zewnętrznych bibliotek. Polski jest silnie fleksyjny, więc przed
   indeksowaniem sprowadzamy słowa do rdzenia: składamy diakrytyki
   (`wynagrodzeń` → `wynagrodzen`), obcinamy końcówki fleksyjne
   (`wynagrodzenia` → `wynagrodz`) i normalizujemy alternację `k`/`c`
   (`pracownicy` → `pracownik`). Dzięki temu „wnioski” i „wniosków” to ten
   sam termin, czego atrapa TF-IDF nie robi.
2. **Wektorowy** — kosinus na wektorach z `EmbeddingPort`. Wektory spraw
   archiwalnych liczone są raz i trzymane w SQLite (`archive_embeddings`),
   więc zapytanie nie płaci za ich ponowne wyliczanie.
3. **Pokrycie terminów** — jaka część (ważona IDF) pojęć z zapytania
   faktycznie występuje w sprawie. To rerank: dwa dokumenty o podobnym
   rankingu rzadko pokrywają zapytanie równie dobrze.

Rankingi leksykalny i wektorowy scalane są reciprocal rank fusion (RRF),
a wynik końcowy to `0.35 * RRF + 0.45 * pokrycie + 0.20 * kosinus`. Pokrycie
waży najwięcej, bo to ono odróżnia sprawę „o tym samym” od sprawy, która
przypadkiem dzieli jedno rzadkie słowo.

**Tryb offline.** Gdy `EmbeddingPort` jest atrapą albo model jest
niedostępny, kanał wektorowy po prostu znika — wyszukiwanie dalej działa na
BM25 i pokryciu terminów. Awaria modelu nigdy nie wywraca zapytania.
"""

from __future__ import annotations

import math
import re
import struct
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import structlog
from sqlalchemy import Engine
from sqlalchemy import text as sql_text

from app.adapters.fakes import fixtures
from app.contracts import ArchiveCase, SimilarCase, SimilarRequest
from app.core.errors import NotFound
from app.ports.inference import EmbeddingPort

log = structlog.get_logger(__name__)

# ──────────────────────────────── parametry ─────────────────────────────────
BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60

#: Waga tematu względem treści wniosku — temat jest zwięzłym streszczeniem.
SUBJECT_WEIGHT = 2.0
#: Waga treści odpowiedzi. Odpowiedź niesie inne słownictwo niż wniosek,
#: więc liczy się słabiej — ma wspierać, nie przesądzać.
RESPONSE_WEIGHT = 0.35

W_RRF = 0.35
W_COVERAGE = 0.45
W_SEMANTIC = 0.20

#: Minimalny kosinus, przy którym sprawa bez wspólnych słów jeszcze wchodzi
#: do wyników. Chroni przed śmieciami z kolizji hashy w atrapie embeddingów —
#: atrapa daje kosinusy rzędu 0,15, więc jej kanał wektorowy jest wyłączony.
MIN_SEMANTIC = 0.35
#: Poniżej tego wyniku sprawa nie jest podobna do zapytania.
MIN_SCORE = 0.02

SNIPPET_CHARS = 240
MAX_MATCHED_TERMS = 6

CACHE_TABLE = "archive_embeddings"
_CACHE_DDL = f"""
CREATE TABLE IF NOT EXISTS {CACHE_TABLE} (
    archive_id TEXT NOT NULL,
    model_key  TEXT NOT NULL,
    dim        INTEGER NOT NULL,
    vector     BLOB NOT NULL,
    PRIMARY KEY (archive_id, model_key)
)
"""

#: Sprawy dopisane przez urzędujących urzędników. Fixtures są tylko do odczytu,
#: więc dorobek pracy urzędu trzymamy osobno i doklejamy do archiwum przy starcie.
CASES_TABLE = "archive_cases"
_CASES_DDL = f"""
CREATE TABLE IF NOT EXISTS {CASES_TABLE} (
    archive_id    TEXT PRIMARY KEY,
    case_number   TEXT NOT NULL UNIQUE,
    subject       TEXT NOT NULL,
    year          INTEGER NOT NULL,
    request_text  TEXT NOT NULL,
    response_text TEXT NOT NULL,
    departments   TEXT NOT NULL DEFAULT ''
)
"""

# ────────────────────────────── normalizacja ────────────────────────────────
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

_WORD = re.compile(r"[a-z0-9]+")
#: Słowo w oryginalnym brzmieniu — potrzebne, żeby pokazać urzędnikowi
#: „wysokością”, a nie złożony rdzeń „wysokoscia”.
_RAW_WORD = re.compile(r"[0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]+")
_YEAR = re.compile(r"^(?:19|20)\d{2}$")

#: Słowa funkcyjne i formuły urzędowe — nie różnicują spraw.
STOPWORDS = frozenset(
    {
        "aby", "albo", "ale", "bez", "bowiem", "byc", "bycia", "bylo", "byly",
        "czy", "dla", "dnia", "dniu", "gdy", "gdzie", "ich", "ile", "inne",
        "innych", "jaki", "jakie", "jego", "jej", "jest", "jesli", "juz",
        "ktora", "ktore", "ktorego", "ktorej", "ktory", "ktorych", "ktorym",
        "lub", "maja", "mial", "miedzy", "moze", "mozna", "nad", "nam", "nas",
        "nie", "nich", "nim", "niz", "oraz", "pod", "podczas", "ponad",
        "poniewaz", "prosba", "prosze", "przez", "przy", "raz", "roku",
        "rowniez", "sie", "sobie", "sposob", "swoje", "tak", "taka", "takie",
        "takze", "tego", "tej", "ten", "tez", "tym", "tych", "tylko", "urzedu",
        "urzedzie", "wedlug", "wiec", "wlasnie", "wniosek", "wnioskiem",
        "wniosku", "wnosze", "wobec", "wraz", "wszystkie", "wszystkich",
        "zostal", "zostaly", "zostalo", "zwracam", "zwracamy", "zwraca",
        # formuły UDIP — występują w niemal każdym wniosku
        "informacja", "informacji", "informacje", "publiczna",
        "publicznej", "publiczne", "udostepnienie", "udostepnienia",
        "udostepnic", "dostep", "dostepu", "dane", "danych", "dana",
    }
)

#: Końcówki fleksyjne, obcinane od najdłuższej. Kolejność ma znaczenie.
_SUFFIXES: tuple[str, ...] = (
    "owania", "owaniu", "owanie",
    "eniami", "aniami",
    "osciami", "oscia", "osci",
    "eniu", "aniu", "enia", "ania", "enie", "anie",
    "acjach", "acjami", "acji", "acja", "acje", "acjo",
    "owych", "owego", "owemu", "owym", "owej",
    "ych", "ich", "ymi", "imi", "ego", "emu",
    "ami", "ach", "owie", "ow",
    "om", "em", "ie", "iu", "ia", "ej", "ym", "im",
    "en", "an", "on",
    "a", "e", "y", "i", "u", "o",
)

_VOWELS = frozenset("aeiouy")
MIN_STEM = 4


def fold(text: str) -> str:
    """Składa diakrytyki i sprowadza do małych liter."""
    return text.lower().translate(_FOLD)


def stem(word: str) -> str:
    """Sprowadza polskie słowo do rdzenia — bez bibliotek fleksyjnych.

    Trzy reguły, celowo proste: obetnij najdłuższą pasującą końcówkę, potem
    wszystkie końcowe samogłoski (`premii` i `premie` muszą dać `prem`),
    a na końcu ujednolić alternację `c` → `k` (`pracownicy` i `pracownik`
    muszą dać ten sam rdzeń).
    """
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_STEM:
            word = word[: -len(suffix)]
            break
    while len(word) > MIN_STEM and word[-1] in _VOWELS:
        word = word[:-1]
    if len(word) > MIN_STEM and word.endswith("c"):
        word = word[:-1] + "k"
    return word


def tokenize(text: str) -> list[str]:
    """Dzieli tekst na rdzenie: diakrytyki złożone, stoplista odrzucona."""
    out: list[str] = []
    for raw in _WORD.findall(fold(text)):
        if _YEAR.match(raw):
            out.append(raw)
            continue
        if len(raw) < 3 or raw in STOPWORDS:
            continue
        out.append(stem(raw))
    return out


def archive_case_uuid(archive_id: str) -> UUID:
    """Stabilny UUID sprawy archiwalnej.

    `SimilarRequest.exclude_case_id` jest UUID-em, a archiwum posługuje się
    krótkimi identyfikatorami (`a0001`). Ten sam algorytm po obu stronach
    pozwala wykluczyć sprawę, którą klient właśnie otworzył.
    """
    return uuid5(NAMESPACE_URL, f"urn:asystent:archiwum:{archive_id}")


def _same_family(left: str, right: str) -> bool:
    """Czy dwa rdzenie to to samo słowo w różnych formach.

    Dokładna równość albo długi wspólny początek — pokrywa resztki
    fleksji, których obcinanie końcówek nie złapało (`pracownic`/`pracownik`).
    """
    if left == right:
        return True
    common = 0
    for a, b in zip(left, right, strict=False):
        if a != b:
            break
        common += 1
    if common < 5:
        return False
    return common >= 0.7 * min(len(left), len(right))


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right, strict=True):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 0.0
    return dot / math.sqrt(left_norm * right_norm)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def _excerpt(text: str, terms: set[str], width: int = SNIPPET_CHARS) -> str:
    """Fragment tekstu wokół zdania najlepiej pokrywającego zapytanie."""
    if not text:
        return ""
    best = ""
    best_hits = -1
    for sentence in _sentences(text):
        hits = sum(1 for token in tokenize(sentence) if token in terms)
        if hits > best_hits:
            best, best_hits = sentence, hits
    if not best:
        best = text.strip()
    if len(best) <= width:
        return best
    return best[: width - 1].rstrip() + "…"


# ──────────────────────────────── dokument ──────────────────────────────────
@dataclass(frozen=True)
class _Doc:
    archive_id: str
    year: int
    case_number: str
    subject: str
    request_text: str
    response_text: str
    departments: tuple[str, ...]
    tf: dict[str, float]
    length: float


class VectorArchiveSearch:
    """Hybrydowe wyszukiwanie podobnych spraw archiwalnych."""

    def __init__(
        self,
        *,
        embedding: EmbeddingPort | None = None,
        engine: Engine | None = None,
        rows: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        self._rows: list[dict[str, Any]] = list(rows if rows is not None else fixtures.archive())
        self._by_id: dict[str, dict[str, Any]] = {row["archive_id"]: row for row in self._rows}
        self._uuid_by_id: dict[str, UUID] = {
            archive_id: archive_case_uuid(archive_id) for archive_id in self._by_id
        }
        self._embedding = embedding
        self._engine = engine
        self._vectors: dict[str, list[float]] | None = None
        self._docs: list[_Doc] = []
        self._idf: dict[str, float] = {}
        self._vocab: list[str] = []
        self._expand_cache: dict[str, list[str]] = {}
        self._avg_len = 1.0
        #: Gdy test podaje `rows`, archiwum jest w pełni zdefiniowane przez
        #: argument — nie dotykamy bazy, żeby nie zależeć od stanu dysku.
        self._explicit_rows = rows is not None
        self._persisted_loaded = False
        self._build_index()

    # ── zależności rozwiązywane leniwie ──
    @property
    def embedding(self) -> EmbeddingPort:
        if self._embedding is None:
            from app.core import container

            self._embedding = container.get_embedding()
        return self._embedding

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            from app.core import db

            self._engine = db.engine
        return self._engine

    # ── indeks leksykalny ──
    def _doc_text(self, archive_id: str) -> str:
        row = self._by_id[archive_id]
        return f"{row['subject']}\n{row['request_text']}"

    def _build_index(self) -> None:
        docs: list[_Doc] = []
        df: Counter[str] = Counter()
        for row in self._rows:
            counts: dict[str, float] = {}
            for token in tokenize(row["subject"]):
                counts[token] = counts.get(token, 0.0) + SUBJECT_WEIGHT
            for token in tokenize(row["request_text"]):
                counts[token] = counts.get(token, 0.0) + 1.0
            for token in tokenize(row["response_text"]):
                counts[token] = counts.get(token, 0.0) + RESPONSE_WEIGHT
            tf = dict(counts)
            docs.append(
                _Doc(
                    archive_id=row["archive_id"],
                    year=int(row["year"]),
                    case_number=row["case_number"],
                    subject=row["subject"],
                    request_text=row["request_text"],
                    response_text=row["response_text"],
                    departments=tuple(row.get("departments") or ()),
                    tf=tf,
                    length=sum(tf.values()),
                )
            )
            df.update(tf.keys())

        total = max(len(docs), 1)
        self._docs = docs
        self._idf = {
            term: math.log(1.0 + (total - count + 0.5) / (count + 0.5))
            for term, count in df.items()
        }
        self._vocab = sorted(self._idf)
        self._avg_len = (sum(doc.length for doc in docs) / total) or 1.0

    # ── sprawy dopisane przez urząd ──
    def _ensure_persisted(self) -> None:
        """Dokleja do archiwum sprawy zapisane w bazie (raz na instancję).

        Fixtures są niezmienne, więc dorobek pracy urzędu trzymamy w osobnej
        tabeli. Doczytujemy go leniwie — konstruktor nie może wymagać bazy,
        bo testy podają `rows` wprost.
        """
        if self._persisted_loaded or self._explicit_rows:
            return
        self._persisted_loaded = True
        try:
            with self.engine.begin() as conn:
                conn.execute(sql_text(_CASES_DDL))
                rows = conn.execute(
                    sql_text(
                        f"SELECT archive_id, case_number, subject, year, "
                        f"request_text, response_text, departments FROM {CASES_TABLE}"
                    )
                ).all()
        except Exception as exc:  # baza tylko do odczytu — zostają same fixtures
            log.warning("archive_persisted_unavailable", error=str(exc))
            return
        if not rows:
            return
        added = False
        for row_tuple in rows:
            archive_id, case_number, subject, year, request_text, response_text, departments = (
                row_tuple
            )
            key = str(archive_id)
            if key in self._by_id:
                continue
            row = {
                "archive_id": key,
                "case_number": str(case_number),
                "subject": str(subject),
                "year": int(year),
                "request_text": str(request_text),
                "response_text": str(response_text),
                "departments": [d for d in str(departments).split(",") if d],
            }
            self._rows.append(row)
            self._by_id[key] = row
            self._uuid_by_id[key] = archive_case_uuid(key)
            added = True
        if added:
            self._build_index()
            self._vectors = None
            self._expand_cache.clear()

    def _next_id(self) -> str:
        """Kolejny identyfikator sprawy dopisanej do archiwum."""
        used = {
            int(aid[1:])
            for aid in self._by_id
            if aid.startswith("n") and aid[1:].isdigit()
        }
        return f"n{max(used, default=0) + 1:04d}"

    def _expand(self, term: str) -> list[str]:
        """Rdzenie z indeksu odpowiadające terminowi z zapytania."""
        cached = self._expand_cache.get(term)
        if cached is not None:
            return cached
        if term in self._idf:
            found = [term]
        else:
            found = [candidate for candidate in self._vocab if _same_family(term, candidate)]
        self._expand_cache[term] = found
        return found

    def _bm25(self, weights: dict[str, float]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for doc in self._docs:
            total = 0.0
            for term, weight in weights.items():
                tf = doc.tf.get(term)
                if not tf:
                    continue
                idf = self._idf.get(term, 0.0)
                norm = BM25_K1 * (1.0 - BM25_B + BM25_B * doc.length / self._avg_len)
                total += weight * idf * (tf * (BM25_K1 + 1.0)) / (tf + norm)
            if total > 0.0:
                scores[doc.archive_id] = total
        return scores

    # ── kanał wektorowy ──
    def _model_key(self) -> str:
        embedding = self.embedding
        return f"{type(embedding).__name__}:{embedding.dim}"

    def _load_cached(self, model_key: str) -> dict[str, list[float]]:
        with self.engine.begin() as conn:
            conn.execute(sql_text(_CACHE_DDL))
            rows = conn.execute(
                sql_text(
                    f"SELECT archive_id, dim, vector FROM {CACHE_TABLE} WHERE model_key = :key"
                ),
                {"key": model_key},
            ).all()
        cached: dict[str, list[float]] = {}
        for archive_id, dim, blob in rows:
            if archive_id not in self._by_id:
                continue
            cached[str(archive_id)] = list(struct.unpack(f"<{int(dim)}f", blob))
        return cached

    def _store_cached(self, model_key: str, vectors: dict[str, list[float]]) -> None:
        payload = [
            {
                "archive_id": archive_id,
                "key": model_key,
                "dim": len(vector),
                "vector": struct.pack(f"<{len(vector)}f", *vector),
            }
            for archive_id, vector in vectors.items()
            if vector
        ]
        if not payload:
            return
        with self.engine.begin() as conn:
            conn.execute(sql_text(_CACHE_DDL))
            conn.execute(
                sql_text(
                    f"INSERT OR REPLACE INTO {CACHE_TABLE} "
                    "(archive_id, model_key, dim, vector) "
                    "VALUES (:archive_id, :key, :dim, :vector)"
                ),
                payload,
            )

    def _ensure_vectors(self) -> dict[str, list[float]]:
        """Wektory spraw archiwalnych — z cache SQLite, brakujące doliczane."""
        if self._vectors is not None:
            return self._vectors

        try:
            model_key = self._model_key()
        except Exception as exc:  # model niedostępny — zostaje sam BM25
            log.warning("archive_embedding_unavailable", error=str(exc))
            self._vectors = {}
            return self._vectors

        try:
            cached = self._load_cached(model_key)
        except Exception as exc:  # baza tylko do odczytu — liczymy w pamięci
            log.warning("archive_embedding_cache_unavailable", error=str(exc))
            cached = {}

        missing = [archive_id for archive_id in self._by_id if archive_id not in cached]
        if missing:
            try:
                fresh = self.embedding.embed([self._doc_text(aid) for aid in missing])
            except Exception as exc:
                log.warning("archive_embedding_failed", error=str(exc), missing=len(missing))
                self._vectors = cached
                return self._vectors
            if len(fresh) != len(missing):
                log.warning(
                    "archive_embedding_count_mismatch",
                    expected=len(missing),
                    received=len(fresh),
                )
            else:
                for archive_id, vector in zip(missing, fresh, strict=True):
                    cached[archive_id] = [float(value) for value in vector]
                try:
                    self._store_cached(model_key, {aid: cached[aid] for aid in missing})
                except Exception as exc:
                    log.warning("archive_embedding_cache_write_failed", error=str(exc))

        self._vectors = cached
        return self._vectors

    def _semantic(self, text: str) -> dict[str, float]:
        vectors = self._ensure_vectors()
        if not vectors:
            return {}
        try:
            query = self.embedding.embed([text])
        except Exception as exc:
            log.warning("archive_query_embedding_failed", error=str(exc))
            return {}
        if not query:
            return {}
        query_vector = [float(value) for value in query[0]]
        scores: dict[str, float] = {}
        for archive_id, vector in vectors.items():
            value = _cosine(query_vector, vector)
            if value > 0.0:
                scores[archive_id] = value
        return scores

    # ── scalanie ──
    @staticmethod
    def _rrf(rankings: Sequence[dict[str, float]]) -> dict[str, float]:
        """Reciprocal rank fusion — suma odwrotności pozycji w rankingach."""
        fused: dict[str, float] = {}
        for ranking in rankings:
            ordered = sorted(ranking.items(), key=lambda item: (-item[1], item[0]))
            for position, (archive_id, _) in enumerate(ordered):
                fused[archive_id] = fused.get(archive_id, 0.0) + 1.0 / (RRF_K + position + 1)
        return fused

    @staticmethod
    def _rrf_ceiling(channels: int) -> float:
        """Wartość RRF sprawy najlepszej we wszystkich aktywnych kanałach."""
        return channels / (RRF_K + 1) if channels else 1.0

    def _query_weights(self, text: str) -> tuple[dict[str, float], dict[str, str]]:
        """Waga IDF każdego pojęcia zapytania i jego forma do pokazania."""
        weights: dict[str, float] = {}
        surface: dict[str, str] = {}
        for original in _RAW_WORD.findall(text):
            raw = fold(original)
            if _YEAR.match(raw):
                term = raw
            elif len(raw) < 3 or raw in STOPWORDS:
                continue
            else:
                term = stem(raw)
            if term in weights:
                continue
            expansions = self._expand(term)
            weights[term] = max((self._idf.get(item, 0.0) for item in expansions), default=0.0)
            surface[term] = original.lower()
        return weights, surface

    def _coverage(self, doc: _Doc, weights: dict[str, float]) -> tuple[float, list[str]]:
        total = sum(weights.values())
        if total <= 0.0:
            return 0.0, []
        matched: list[str] = []
        covered = 0.0
        for term, weight in weights.items():
            if any(candidate in doc.tf for candidate in self._expand(term)):
                covered += weight
                matched.append(term)
        return covered / total, matched

    # ── port ──
    def similar(self, req: SimilarRequest) -> list[SimilarCase]:
        self._ensure_persisted()
        text = (req.text or "").strip()
        if not text:
            return []

        weights, surface = self._query_weights(text)
        if not weights:
            return []

        excluded = {req.exclude_case_id} if req.exclude_case_id else set()

        candidates: list[_Doc] = []
        for doc in self._docs:
            if req.year_from is not None and doc.year < req.year_from:
                continue
            if self._uuid_by_id[doc.archive_id] in excluded:
                continue
            candidates.append(doc)
        if not candidates:
            return []

        lexical = self._bm25(weights)
        semantic = self._semantic(text)

        allowed = {doc.archive_id for doc in candidates}
        lexical = {aid: value for aid, value in lexical.items() if aid in allowed}
        semantic = {
            aid: value
            for aid, value in semantic.items()
            if aid in allowed and value >= MIN_SEMANTIC
        }

        pool = set(lexical) | set(semantic)
        if not pool:
            return []

        channels = [ranking for ranking in (lexical, semantic) if ranking]
        fused = self._rrf(channels)
        ceiling = self._rrf_ceiling(len(channels))

        scored: list[tuple[float, _Doc, list[str]]] = []
        for doc in candidates:
            if doc.archive_id not in pool:
                continue
            coverage, matched = self._coverage(doc, weights)
            rrf_norm = min(fused.get(doc.archive_id, 0.0) / ceiling, 1.0)
            semantic_score = max(semantic.get(doc.archive_id, 0.0), 0.0)
            score = W_RRF * rrf_norm + W_COVERAGE * coverage + W_SEMANTIC * semantic_score
            score = min(max(score, 0.0), 1.0)
            if score < MIN_SCORE:
                continue
            scored.append((score, doc, matched))

        scored.sort(key=lambda item: (-item[0], item[1].archive_id))

        results: list[SimilarCase] = []
        for score, doc, matched in scored[: req.k]:
            terms = sorted(matched, key=lambda term: (-weights.get(term, 0.0), term))
            shown = [surface.get(term, term) for term in terms[:MAX_MATCHED_TERMS]]
            # Fragmenty wybieramy po rdzeniach z indeksu, nie po formach zapytania —
            # inaczej „premie” nie zaznaczyłoby zdania z „premii”.
            stems = {candidate for term in matched for candidate in self._expand(term)}
            results.append(
                SimilarCase(
                    archive_id=doc.archive_id,
                    case_number=doc.case_number,
                    subject=doc.subject,
                    year=doc.year,
                    score=round(score, 4),
                    snippet=_excerpt(doc.request_text, stems),
                    matched_terms=shown,
                    response_excerpt=_excerpt(doc.response_text, stems),
                )
            )
        return results

    def get(self, archive_id: str) -> ArchiveCase:
        self._ensure_persisted()
        row = self._by_id.get(archive_id)
        if row is None:
            raise NotFound("Nie znaleziono sprawy archiwalnej.")
        return ArchiveCase(**row)

    def size(self) -> int:
        self._ensure_persisted()
        return len(self._rows)

    def add(self, case: ArchiveCase) -> str:
        """Dopisuje sprawę do archiwum — trwale, w tabeli `archive_cases`."""
        self._ensure_persisted()
        for aid, row in self._by_id.items():
            if row["case_number"] == case.case_number:
                return aid

        archive_id = case.archive_id or self._next_id()
        row = {
            "archive_id": archive_id,
            "case_number": case.case_number,
            "subject": case.subject,
            "year": case.year,
            "request_text": case.request_text,
            "response_text": case.response_text,
            "departments": list(case.departments),
        }
        try:
            with self.engine.begin() as conn:
                conn.execute(sql_text(_CASES_DDL))
                conn.execute(
                    sql_text(
                        f"INSERT OR REPLACE INTO {CASES_TABLE} "
                        "(archive_id, case_number, subject, year, request_text, "
                        "response_text, departments) "
                        "VALUES (:archive_id, :case_number, :subject, :year, "
                        ":request_text, :response_text, :departments)"
                    ),
                    {**row, "departments": ",".join(case.departments)},
                )
        except Exception as exc:
            # Archiwum w pamięci i tak się powiększy — tracimy tylko trwałość.
            log.warning("archive_persist_failed", error=str(exc), archive_id=archive_id)

        self._rows.append(row)
        self._by_id[archive_id] = row
        self._uuid_by_id[archive_id] = archive_case_uuid(archive_id)
        self._build_index()
        self._vectors = None
        self._expand_cache.clear()
        return archive_id
