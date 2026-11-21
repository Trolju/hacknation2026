"""Źródła projektu odpowiedzi: przepisy, archiwum i dokumenty sprawy.

Każde źródło dostaje numer (`ref`), którym posługuje się treść projektu
w odnośnikach `[^n]`. Numeracja jest deterministyczna: najpierw przepisy,
potem sprawy zbliżone z archiwum, odpowiedzi komórek i dokumenty sprawy.
Dzięki temu ten sam zestaw danych zawsze daje ten sam projekt — również
wtedy, gdy model językowy jest niedostępny i treść powstaje z szablonu.

Podstawa prawna (W8) powstaje z dwóch miejsc: z plików `fixtures/statutes/`
oraz z ustaw i zarządzeń wgranych do bazy wiedzy. Wgrany akt dzieli się na
artykuły i paragrafy tym samym `_articles()`, co pliki z fixtures, więc oba
źródła zachowują się identycznie — różnią się tylko pochodzeniem.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from uuid import UUID

from app.contracts import CaseDetail, Citation, DocumentKind, SimilarRequest
from app.core.errors import AppError
from app.core.settings import settings
from app.ports.archive import ArchiveSearchPort
from app.ports.documents import DocumentStorePort

SourceType = Literal["document", "archive", "statute", "department_reply"]

EXCERPT_CHARS = 240
MAX_ARCHIVE = 3
MAX_DOCUMENTS = 4
# Wgrana ustawa bywa długa (KPA ma ponad 200 artykułów), a prompt ma limit.
# Bierzemy pierwsze artykuły w kolejności dokumentu — deterministycznie.
MAX_STATUTE_ARTICLES = 12

# Rodzaje dokumentów, które są podstawą prawną, a nie dokumentem sprawy.
_KNOWLEDGE_KINDS: tuple[DocumentKind, ...] = (
    DocumentKind.USTAWA,
    DocumentKind.ZARZADZENIE,
)

_ARTICLE_HEADER = re.compile(r"^(Art\.\s*\d+[a-z]?\.|§\s*\d+\.)", re.MULTILINE)
_WHITESPACE = re.compile(r"\s+")
_NON_WORD = re.compile(r"[^0-9a-ząćęłńóśźż]+")


@dataclass(frozen=True)
class Source:
    """Pojedyncze źródło twierdzenia wraz z numerem odnośnika."""

    ref: int
    source_type: SourceType
    source_id: str
    label: str
    excerpt: str
    text: str

    def citation(self) -> Citation:
        return Citation(
            ref=self.ref,
            source_type=self.source_type,
            source_id=self.source_id,
            label=self.label,
            excerpt=self.excerpt,
        )


@dataclass(frozen=True)
class _Provision:
    """Przepis, który zawsze wchodzi do podstawy prawnej odpowiedzi."""

    statute: str
    article: str
    label: str


_PROVISIONS: tuple[_Provision, ...] = (
    _Provision(
        statute="udip",
        article="Art. 13.",
        label="art. 13 ust. 1 i 2 ustawy o dostępie do informacji publicznej",
    ),
    _Provision(
        statute="udip",
        article="Art. 10.",
        label="art. 10 ust. 1 ustawy o dostępie do informacji publicznej",
    ),
    _Provision(
        statute="udip",
        article="Art. 5.",
        label="art. 5 ust. 2 ustawy o dostępie do informacji publicznej",
    ),
    _Provision(
        statute="udip",
        article="Art. 16.",
        label="art. 16 ustawy o dostępie do informacji publicznej",
    ),
    _Provision(
        statute="zarzadzenie-412-2023",
        article="§ 4.",
        label="§ 4 zarządzenia nr 412/2023 Prezydenta Miasta Bydgoszczy",
    ),
)


# ─────────────────────────────── pomocnicze ────────────────────────────────
def _excerpt(text: str, limit: int = EXCERPT_CHARS) -> str:
    """Skrót tekstu do panelu cytowań — bez wielokrotnych spacji i nowych linii."""
    cleaned = _WHITESPACE.sub(" ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rsplit(" ", 1)[0] + "…"


def _read_statute(name: str) -> str:
    path: Path = settings.fixtures_dir / "statutes" / f"{name}.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _articles(text: str) -> dict[str, str]:
    """Dzieli tekst aktu prawnego na bloki `Art. N.` / `§ N.`."""
    matches = list(_ARTICLE_HEADER.finditer(text))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = _WHITESPACE.sub(" ", match.group(1)).strip()
        blocks[key] = _WHITESPACE.sub(" ", text[match.start() : end]).strip()
    return blocks


def _first_line(text: str) -> str:
    """Pierwsza niepusta linia tekstu — nagłówek aktu prawnego."""
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return ""


def _slug(text: str) -> str:
    """Klucz porównania tytułów: małe litery, bez interpunkcji i nadmiaru spacji."""
    return _NON_WORD.sub(" ", text.lower()).strip()


def _fixture_titles() -> dict[str, str]:
    """Mapa „znormalizowany tytuł → nazwa pliku z fixtures/statutes/”.

    Tytułem pliku jest zarówno nazwa bez rozszerzenia (`udip`), jak i nagłówek
    aktu z pierwszej linii („USTAWA z dnia 6 września 2001 r. o dostępie do
    informacji publicznej”). Dzięki temu wgranie nowego tekstu ustawy pod
    którąkolwiek z tych nazw przykrywa plik z fixtures.
    """
    directory: Path = settings.fixtures_dir / "statutes"
    if not directory.is_dir():
        return {}
    titles: dict[str, str] = {}
    for path in sorted(directory.glob("*.txt")):
        titles[_slug(path.stem)] = path.stem
        heading = _first_line(_read_statute(path.stem))
        if heading:
            titles.setdefault(_slug(heading), path.stem)
    return titles


def _article_label(article: str) -> str:
    """„Art. 13.” → „art. 13”, „§ 4.” → „§ 4” — numer przepisu w etykiecie."""
    trimmed = article.rstrip(".")
    return trimmed.lower() if trimmed.startswith("Art.") else trimmed


def _uploaded_statutes(
    documents: DocumentStorePort,
) -> tuple[list[Source], set[str]]:
    """Artykuły wgranych ustaw i zarządzeń oraz nazwy przykrytych plików fixtures.

    Dokumenty czytamy z bazy wiedzy (rodzaj `ustawa` / `zarzadzenie`), dzielimy
    tym samym `_articles()`, co pliki z fixtures, i zamieniamy na źródła typu
    `statute`. `source_id` zawiera identyfikator dokumentu, więc kolejne wersje
    tej samej ustawy nie zlewają się ze sobą w deduplikacji `collect_sources`.
    """
    titles = _fixture_titles()
    overridden: set[str] = set()
    sources: list[Source] = []
    for kind in _KNOWLEDGE_KINDS:
        try:
            rows = documents.list(kind=kind)
        except AppError:
            continue
        for row in rows:
            try:
                detail = documents.get(row.id)
            except AppError:
                continue
            title = detail.title or detail.filename
            for key in (_slug(title), _slug(Path(detail.filename).stem)):
                fixture = titles.get(key)
                if fixture is not None:
                    overridden.add(fixture)
            articles = _articles(detail.text)
            for article, body in list(articles.items())[:MAX_STATUTE_ARTICLES]:
                sources.append(
                    Source(
                        ref=0,
                        source_type="statute",
                        source_id=f"{detail.id}#{article}",
                        label=f"{_article_label(article)} — {title}",
                        excerpt=_excerpt(body),
                        text=body,
                    )
                )
    return sources, overridden


# ──────────────────────────────── przepisy ─────────────────────────────────
def statute_sources(documents: DocumentStorePort | None = None) -> list[Source]:
    """Podstawa prawna odpowiedzi: przepisy z fixtures i wgrane akty prawne.

    Kolejność jest stała: najpierw przepisy wybrane z `fixtures/statutes/`
    (w kolejności `_PROVISIONS`), potem artykuły i paragrafy ustaw oraz
    zarządzeń wgranych do bazy wiedzy (rodzaj `ustawa` / `zarzadzenie`).

    Kolizja tytułów — aktualizacja ustawy: gdy wgrany dokument ma tytuł albo
    nazwę pliku taką samą jak plik z fixtures, wygrywa wersja wgrana. Plik
    z fixtures znika wtedy z podstawy prawnej w całości, a jego miejsce
    zajmują artykuły wgranego aktu. Urzędnik aktualizuje więc tekst ustawy,
    wgrywając nowy dokument — bez zmian w kodzie i bez duplikatów w piśmie.

    `documents=None` oznacza samą bazę fixtures; tak woła tę funkcję każdy,
    kto nie ma dostępu do magazynu dokumentów.
    """
    uploaded: list[Source] = []
    overridden: set[str] = set()
    if documents is not None:
        uploaded, overridden = _uploaded_statutes(documents)

    cache: dict[str, dict[str, str]] = {}
    sources: list[Source] = []
    for provision in _PROVISIONS:
        if provision.statute in overridden:
            continue
        if provision.statute not in cache:
            cache[provision.statute] = _articles(_read_statute(provision.statute))
        body = cache[provision.statute].get(provision.article)
        if not body:
            continue
        sources.append(
            Source(
                ref=0,
                source_type="statute",
                source_id=f"{provision.statute}#{provision.article}",
                label=provision.label,
                excerpt=_excerpt(body),
                text=body,
            )
        )
    sources.extend(uploaded)
    return sources


# ──────────────────────────────── archiwum ─────────────────────────────────
def _archive_sources(case: CaseDetail, archive: ArchiveSearchPort) -> list[Source]:
    query = f"{case.subject}. {case.notes or ''}".strip()
    try:
        rows = archive.similar(
            SimilarRequest(text=query, k=MAX_ARCHIVE, exclude_case_id=case.id)
        )
    except AppError:
        return []
    return [
        Source(
            ref=0,
            source_type="archive",
            source_id=row.archive_id,
            label=f"{row.case_number} — {row.subject}",
            excerpt=_excerpt(row.response_excerpt or row.snippet),
            text=row.response_excerpt or row.snippet,
        )
        for row in rows
    ]


# ──────────────────────────────── dokumenty ────────────────────────────────
def _reply_sources(
    reply_ids: list[UUID], documents: DocumentStorePort
) -> list[Source]:
    sources: list[Source] = []
    for document_id in reply_ids:
        try:
            detail = documents.get(document_id)
        except AppError:
            continue
        sources.append(
            Source(
                ref=0,
                source_type="department_reply",
                source_id=str(detail.id),
                label=f"Odpowiedź komórki: {detail.title or detail.filename}",
                excerpt=_excerpt(detail.text),
                text=detail.text,
            )
        )
    return sources


def _document_sources(case: CaseDetail, documents: DocumentStorePort) -> list[Source]:
    ordered: list[UUID] = []
    # Skan wniosku podpięty do sprawy jest źródłem tak samo jak pliki wgrane
    # później. Bez tego projektu nie dało się oprzeć na samym wniosku, gdy
    # dokument trafił do akt przez `source_document_id`, a nie przez `case_id`.
    if case.source_document_id is not None:
        ordered.append(case.source_document_id)
    with contextlib.suppress(AppError):
        for document in documents.list(case_id=case.id):
            if document.id not in ordered:
                ordered.append(document.id)
    for document_id in case.document_ids:
        if document_id not in ordered:
            ordered.append(document_id)

    sources: list[Source] = []
    for document_id in ordered:
        if len(sources) >= MAX_DOCUMENTS:
            break
        try:
            detail = documents.get(document_id)
        except AppError:
            continue
        if detail.kind in _KNOWLEDGE_KINDS:
            # Ustawa i zarządzenie są podstawą prawną (statute_sources), a nie
            # dokumentem sprawy — inaczej ten sam akt trafiłby do pisma dwa razy.
            continue
        sources.append(
            Source(
                ref=0,
                source_type="document",
                source_id=str(detail.id),
                label=detail.title or detail.filename,
                excerpt=_excerpt(detail.text),
                text=detail.text,
            )
        )
    return sources


# ──────────────────────────────── zestawienie ──────────────────────────────
def collect_sources(
    case: CaseDetail,
    *,
    use_archive: bool,
    use_statutes: bool,
    department_reply_ids: list[UUID],
    archive: ArchiveSearchPort,
    documents: DocumentStorePort,
) -> list[Source]:
    """Zbiera źródła i nadaje im kolejne numery odnośników."""
    collected: list[Source] = []
    if use_statutes:
        collected.extend(statute_sources(documents))
    if use_archive:
        collected.extend(_archive_sources(case, archive))
    collected.extend(_reply_sources(department_reply_ids, documents))
    collected.extend(_document_sources(case, documents))

    unique: list[Source] = []
    seen: set[str] = set()
    for source in collected:
        if source.source_id in seen:
            continue
        seen.add(source.source_id)
        unique.append(source)
    return [replace(source, ref=index) for index, source in enumerate(unique, start=1)]
