"""Realny adapter dokumentów (WS2).

Kontener szuka w tym module dwóch klas:

- `PdfDocxParser` — ekstrakcja tekstu z PDF (`pdfplumber`), DOCX (`python-docx`)
  oraz TXT/MD, a także chunkowanie z zachowaniem offsetów,
- `SqlDocumentStore` — magazyn dokumentów i fragmentów w SQLite (SQLAlchemy 2.0).

Granice stron w tekście znaczy znak form feed (`\\f`). Dzięki temu każdy
fragment dostaje numer strony bez zmiany zamrożonego portu `DocumentParserPort`,
którego `chunk()` widzi wyłącznie tekst.
"""

from __future__ import annotations

import hashlib
import io
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy import text as sql_text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.contracts import (
    Chunk,
    Document,
    DocumentDetail,
    DocumentKind,
    DocumentStatus,
)
from app.core import db
from app.core.clock import now as clock_now
from app.core.db import Base
from app.core.errors import Conflict, NotFound, UnsupportedMedia
from app.modules.ingest.models import DocumentChunkRow, DocumentRow

log = structlog.get_logger(__name__)

CHUNK_CHARS = 900
CHUNK_OVERLAP = 120
PAGE_BREAK = "\f"

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_BY_SUFFIX = {
    ".pdf": "application/pdf",
    ".docx": DOCX_MIME,
    ".txt": "text/plain",
    ".md": "text/markdown",
}

# Rodzaje, dla których ponowne wgranie tego samego pliku ma nadpisać wpis
# (baza wiedzy), a nie utworzyć duplikat.
KNOWLEDGE_KINDS = frozenset({DocumentKind.USTAWA, DocumentKind.ZARZADZENIE})

# Alias, bo wewnątrz klasy `SqlDocumentStore` nazwa `list` oznacza metodę.
ChunkList = list[Chunk]

_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s+\S|Rozdział\s+\S|Dział\s+\S|§\s*\d|Art\.\s*\d|USTAWA\b|ZARZĄDZENIE\b)",
    re.IGNORECASE,
)


# ─────────────────────────────── komunikaty ────────────────────────────────
def unsupported_message(suffix: str) -> str:
    """Czytelny komunikat po polsku dla nieobsługiwanego formatu."""
    if suffix == ".doc":
        return (
            "Format .doc nie jest obsługiwany. Zapisz dokument jako .docx "
            "i wgraj go ponownie."
        )
    if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}:
        return (
            "Pliki graficzne nie są obsługiwane. Wgraj dokument PDF z warstwą "
            "tekstową albo plik DOCX."
        )
    if suffix in {".exe", ".bat", ".cmd", ".sh", ".msi", ".dll", ".js"}:
        return (
            f"Plik {suffix} nie jest dokumentem. Wgraj plik PDF, DOCX, TXT albo MD."
        )
    label = suffix or "bez rozszerzenia"
    return (
        f"Nieobsługiwany format pliku ({label}). "
        "Obsługiwane formaty: PDF, DOCX, TXT, MD."
    )


def _normalize(text: str) -> str:
    """Ujednolica końce linii i usuwa nadmiar pustych linii."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(PAGE_BREAK, "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ──────────────────────────────── parser ───────────────────────────────────
class PdfDocxParser:
    """Parser PDF/DOCX/TXT/MD zgodny z `DocumentParserPort`."""

    def parse(self, blob: bytes, filename: str) -> tuple[str, int]:
        """Zwraca (tekst, liczba_stron). Strony rozdziela znak `\\f`."""
        suffix = Path(filename).suffix.lower()
        if not blob:
            raise UnsupportedMedia("Plik jest pusty — nie ma czego odczytać.")
        if suffix == ".pdf":
            return self._parse_pdf(blob)
        if suffix == ".docx":
            return self._parse_docx(blob)
        if suffix in {".txt", ".md"}:
            return self._parse_text(blob)
        raise UnsupportedMedia(unsupported_message(suffix))

    # ── formaty ──
    def _parse_pdf(self, blob: bytes) -> tuple[str, int]:
        import pdfplumber

        try:
            with pdfplumber.open(io.BytesIO(blob)) as pdf:
                pages = [_normalize(page.extract_text() or "") for page in pdf.pages]
        except Exception as exc:  # biblioteka rzuca różne typy przy uszkodzonym pliku
            raise UnsupportedMedia(
                "Nie udało się odczytać pliku PDF — plik jest uszkodzony "
                "albo zabezpieczony hasłem."
            ) from exc
        if not any(pages):
            raise UnsupportedMedia(
                "Dokument PDF nie zawiera warstwy tekstowej — to najprawdopodobniej "
                "skan. Wgraj plik po rozpoznaniu tekstu (OCR) albo wersję tekstową."
            )
        # końcowy separator sprawia, że także jednostronicowy PDF jest „paginowany”
        return PAGE_BREAK.join(pages) + PAGE_BREAK, len(pages)

    def _parse_docx(self, blob: bytes) -> tuple[str, int]:
        import docx

        try:
            document = docx.Document(io.BytesIO(blob))
        except Exception as exc:
            raise UnsupportedMedia(
                "Nie udało się odczytać pliku DOCX — plik jest uszkodzony "
                "albo zabezpieczony hasłem."
            ) from exc
        blocks = [_normalize(paragraph.text) for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                cells = [_normalize(cell.text) for cell in row.cells]
                line = " | ".join(cell for cell in cells if cell)
                if line:
                    blocks.append(line)
        text = "\n\n".join(block for block in blocks if block)
        if not text.strip():
            raise UnsupportedMedia(
                "Dokument DOCX nie zawiera tekstu — sprawdź, czy treść nie jest "
                "osadzona jako obraz."
            )
        return text, 1

    def _parse_text(self, blob: bytes) -> tuple[str, int]:
        if b"\x00" in blob[:4096]:
            raise UnsupportedMedia(
                "Plik tekstowy zawiera dane binarne — to nie jest plik TXT ani MD."
            )
        text = _normalize(blob.decode("utf-8", errors="replace"))
        if not text.strip():
            raise UnsupportedMedia("Plik tekstowy jest pusty.")
        return text, 1

    # ── chunkowanie ──
    def chunk(self, text: str, *, document_id: UUID) -> list[Chunk]:
        """Dzieli tekst na fragmenty ~900 znaków z zakładką 120 znaków.

        Cięcie wypada na granicy akapitu, a gdy akapit jest dłuższy — na końcu
        zdania albo wyrazu. Fragment nigdy nie przekracza granicy strony, więc
        każdy niesie `page` (PDF) albo `section` (DOCX/TXT/MD).
        """
        chunks: list[Chunk] = []
        index = 0
        for page_number, page_text, page_offset in _split_pages(text):
            for start, end in _windows(page_text):
                body = page_text[start:end].strip()
                if not body:
                    continue
                chunks.append(
                    Chunk(
                        id=f"{document_id}:{index}",
                        document_id=document_id,
                        index=index,
                        text=body,
                        page=page_number,
                        section=(
                            None
                            if page_number is not None
                            else _section_for(text, page_offset + start)
                        ),
                    )
                )
                index += 1
        return chunks


def _split_pages(text: str) -> list[tuple[int | None, str, int]]:
    """Dzieli tekst na strony: (numer_strony, tekst, offset_w_tekście)."""
    if PAGE_BREAK not in text:
        return [(None, text, 0)]
    parts = text.split(PAGE_BREAK)
    if parts and not parts[-1]:
        parts.pop()  # końcowy separator nie tworzy pustej strony
    pages: list[tuple[int | None, str, int]] = []
    offset = 0
    for number, page in enumerate(parts, start=1):
        pages.append((number, page, offset))
        offset += len(page) + len(PAGE_BREAK)
    return pages


def _windows(text: str) -> list[tuple[int, int]]:
    """Okna [start, end) o długości do CHUNK_CHARS z zakładką CHUNK_OVERLAP."""
    spans: list[tuple[int, int]] = []
    length = len(text)
    start = 0
    while start < length:
        end = min(start + CHUNK_CHARS, length)
        if end < length:
            cut = _cut_point(text, start, end)
            if cut is not None:
                end = cut
        spans.append((start, end))
        if end >= length:
            break
        next_start = max(end - CHUNK_OVERLAP, start + 1)
        # nie zaczynaj fragmentu w środku wyrazu
        while next_start < end and not text[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return spans


def _cut_point(text: str, start: int, end: int) -> int | None:
    """Najlepsze miejsce cięcia w oknie [start + połowa, end)."""
    floor = start + CHUNK_CHARS // 2
    for marker in ("\n\n", "\n", ". ", "; ", " "):
        position = text.rfind(marker, floor, end)
        if position != -1:
            return position + len(marker)
    return None


def _section_for(text: str, offset: int) -> str | None:
    """Najbliższy nagłówek przed offsetem; w razie braku — pierwsza linia."""
    window_start = max(0, offset - 4000)
    for line in reversed(text[window_start:offset].split("\n")):
        candidate = line.strip()
        if candidate and _is_heading(candidate):
            return candidate[:160]
    return _first_line(text)


def _is_heading(line: str) -> bool:
    if _HEADING_RE.match(line):
        return True
    if len(line) > 120:
        return False
    letters = [char for char in line if char.isalpha()]
    return len(letters) >= 3 and line.isupper()


def _first_line(text: str) -> str | None:
    for line in text.split("\n"):
        candidate = line.strip()
        if candidate:
            return candidate[:160]
    return None


# ──────────────────────────────── magazyn ──────────────────────────────────
def _default_upload_dir() -> Path:
    raw = os.getenv("UPLOAD_DIR")
    return Path(raw) if raw else Path("data") / "uploads"


def detect_mime(filename: str, blob: bytes) -> str:
    """Sprawdza format po zawartości pliku, nie tylko po rozszerzeniu."""
    suffix = Path(filename).suffix.lower()
    mime = MIME_BY_SUFFIX.get(suffix)
    if mime is None:
        raise UnsupportedMedia(unsupported_message(suffix))
    if not blob:
        raise UnsupportedMedia("Plik jest pusty — nie ma czego odczytać.")
    if suffix == ".pdf" and not blob.startswith(b"%PDF"):
        raise UnsupportedMedia(
            "Plik ma rozszerzenie .pdf, ale nie jest dokumentem PDF."
        )
    if suffix == ".docx" and not blob.startswith(b"PK"):
        raise UnsupportedMedia(
            "Plik ma rozszerzenie .docx, ale nie jest dokumentem Word."
        )
    if suffix in {".txt", ".md"} and b"\x00" in blob[:4096]:
        raise UnsupportedMedia(
            "Plik tekstowy zawiera dane binarne — to nie jest plik TXT ani MD."
        )
    return mime


class SqlDocumentStore:
    """Magazyn dokumentów w SQLite; pliki źródłowe leżą w `data/uploads/`."""

    def __init__(
        self,
        parser: PdfDocxParser | None = None,
        *,
        engine: Engine | None = None,
        upload_dir: Path | str | None = None,
    ) -> None:
        self._parser = parser or PdfDocxParser()
        self._engine = engine if engine is not None else db.engine
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, expire_on_commit=False
        )
        self._upload_dir = Path(upload_dir) if upload_dir is not None else _default_upload_dir()
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(
            bind=self._engine,
            tables=[DocumentRow.__table__, DocumentChunkRow.__table__],  # type: ignore[list-item]
        )
        self._ensure_columns()

    def _ensure_columns(self) -> None:
        """Dokłada kolumny dodane po pierwszym uruchomieniu.

        `create_all` tworzy tylko brakujące tabele — istniejącej bazy nie
        zmienia. Bez tego baza z poprzedniej wersji kończyłaby się błędem
        „no such column: documents.content_hash”.
        """
        try:
            with self._engine.begin() as conn:
                existing = {
                    row[1]
                    for row in conn.execute(
                        sql_text("PRAGMA table_info(documents)")
                    ).all()
                }
                if existing and "content_hash" not in existing:
                    conn.execute(
                        sql_text("ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64)")
                    )
        except Exception:  # nie-SQLite albo baza tylko do odczytu
            pass

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    # ── odczyt ──
    def list(
        self, *, kind: DocumentKind | None = None, case_id: UUID | None = None
    ) -> list[Document]:
        with self._session_factory() as session:
            stmt = select(DocumentRow).order_by(DocumentRow.created_at.desc())
            if kind is not None:
                stmt = stmt.where(DocumentRow.kind == kind.value)
            if case_id is not None:
                stmt = stmt.where(DocumentRow.case_id == str(case_id))
            return [_to_document(row) for row in session.scalars(stmt)]

    def get(self, document_id: UUID) -> DocumentDetail:
        with self._session_factory() as session:
            row = session.get(DocumentRow, str(document_id))
            if row is None:
                raise NotFound("Nie znaleziono dokumentu.")
            return _to_detail(row)

    def chunks(self, document_id: UUID) -> ChunkList:
        with self._session_factory() as session:
            if session.get(DocumentRow, str(document_id)) is None:
                raise NotFound("Nie znaleziono dokumentu.")
            rows = session.scalars(
                select(DocumentChunkRow)
                .where(DocumentChunkRow.document_id == str(document_id))
                .order_by(DocumentChunkRow.index)
            )
            return [_to_chunk(row) for row in rows]

    # ── zapis ──
    def create(
        self,
        *,
        blob: bytes,
        filename: str,
        kind: DocumentKind,
        case_id: UUID | None = None,
        title: str | None = None,
    ) -> Document:
        safe_name = Path(filename).name or "plik"
        mime = detect_mime(safe_name, blob)
        content_hash = hashlib.sha256(blob).hexdigest()
        # Zegar aplikacji — w demo data jest zakotwiczona na `DEMO_TODAY`.
        now = clock_now()

        with self._session_factory() as session:
            row = self._find_replaceable(session, kind, safe_name, case_id)
            if row is None:
                # Ten sam plik wgrany drugi raz nie tworzy nowego wpisu.
                # Wcześniej baza wiedzy zapełniała się duplikatami, które
                # trzeba było usuwać ręcznie.
                duplicate = self._find_duplicate(session, kind, content_hash, case_id)
                if duplicate is not None:
                    log.info(
                        "document_duplicate_skipped",
                        document_id=duplicate.id,
                        filename=safe_name,
                    )
                    return _to_document(duplicate)
            document_id = UUID(row.id) if row is not None else uuid4()
            stored_path = self._write_file(document_id, safe_name, blob)
            if row is not None and row.storage_path and row.storage_path != str(stored_path):
                _remove_file(row.storage_path)

            text, page_count, chunks, status, error = self._parse(
                blob, safe_name, document_id
            )
            values = {
                "kind": kind.value,
                "filename": safe_name,
                "title": title or Path(safe_name).stem,
                "mime": mime,
                "size_bytes": len(blob),
                "status": status.value,
                "error": error,
                "case_id": str(case_id) if case_id is not None else None,
                "chunk_count": len(chunks),
                "page_count": page_count,
                "text": text,
                "storage_path": str(stored_path),
                "content_hash": content_hash,
            }
            if row is None:
                row = DocumentRow(id=str(document_id), created_at=now, **values)
                session.add(row)
            else:
                for key, value in values.items():
                    setattr(row, key, value)
                row.updated_at = now
                session.execute(
                    delete(DocumentChunkRow).where(
                        DocumentChunkRow.document_id == row.id
                    )
                )
            session.flush()
            session.add_all(_chunk_rows(document_id, chunks))
            session.commit()
            log.info(
                "document_stored",
                document_id=str(document_id),
                kind=kind.value,
                status=status.value,
                size_bytes=len(blob),
                chunk_count=len(chunks),
            )
            return _to_document(row)

    def delete(self, document_id: UUID) -> None:
        with self._session_factory() as session:
            row = session.get(DocumentRow, str(document_id))
            if row is None:
                raise NotFound("Nie znaleziono dokumentu.")
            storage_path = row.storage_path
            session.execute(
                delete(DocumentChunkRow).where(DocumentChunkRow.document_id == row.id)
            )
            session.delete(row)
            session.commit()
        _remove_file(storage_path)
        log.info("document_deleted", document_id=str(document_id))

    def reindex(self, document_id: UUID) -> Document:
        with self._session_factory() as session:
            row = session.get(DocumentRow, str(document_id))
            if row is None:
                raise NotFound("Nie znaleziono dokumentu.")
            blob = _read_file(row.storage_path)
            if blob is None:
                raise Conflict(
                    "Brak pliku źródłowego dokumentu — wgraj dokument ponownie."
                )
            text, page_count, chunks, status, error = self._parse(
                blob, row.filename, document_id
            )
            row.text = text
            row.page_count = page_count
            row.status = status.value
            row.error = error
            row.chunk_count = len(chunks)
            row.updated_at = clock_now()
            session.execute(
                delete(DocumentChunkRow).where(DocumentChunkRow.document_id == row.id)
            )
            session.add_all(_chunk_rows(document_id, chunks))
            session.commit()
            log.info(
                "document_reindexed",
                document_id=str(document_id),
                status=status.value,
                chunk_count=len(chunks),
            )
            return _to_document(row)

    # ── pomocnicze ──
    def _parse(
        self, blob: bytes, filename: str, document_id: UUID
    ) -> tuple[str, int, ChunkList, DocumentStatus, str | None]:
        try:
            text, page_count = self._parser.parse(blob, filename)
            chunks = self._parser.chunk(text, document_id=document_id)
        except UnsupportedMedia as exc:
            log.warning(
                "document_parse_failed",
                document_id=str(document_id),
                reason=exc.code,
            )
            return "", 0, [], DocumentStatus.FAILED, exc.message
        return text, page_count, chunks, DocumentStatus.INDEXED, None

    def _find_replaceable(
        self,
        session: Session,
        kind: DocumentKind,
        filename: str,
        case_id: UUID | None,
    ) -> DocumentRow | None:
        """Wpis do nadpisania przy ponownym wgraniu ustawy lub zarządzenia."""
        if kind not in KNOWLEDGE_KINDS or case_id is not None:
            return None
        stmt = select(DocumentRow).where(
            DocumentRow.kind == kind.value,
            func.lower(DocumentRow.filename) == filename.lower(),
        )
        return session.scalars(stmt).first()

    def _find_duplicate(
        self,
        session: Session,
        kind: DocumentKind,
        content_hash: str,
        case_id: UUID | None,
    ) -> DocumentRow | None:
        """Wpis o tej samej treści — ten sam plik wgrany ponownie.

        Porównujemy skrót treści, nie nazwę: zmiana nazwy pliku nie tworzy
        drugiego wpisu, a poprawiona treść pod tą samą nazwą tworzy nowy.
        """
        stmt = select(DocumentRow).where(
            DocumentRow.kind == kind.value,
            DocumentRow.content_hash == content_hash,
            DocumentRow.case_id == (str(case_id) if case_id is not None else None),
        )
        return session.scalars(stmt).first()

    def _write_file(self, document_id: UUID, filename: str, blob: bytes) -> Path:
        path = self._upload_dir / f"{document_id}{Path(filename).suffix.lower()}"
        path.write_bytes(blob)
        return path


def _chunk_rows(document_id: UUID, chunks: ChunkList) -> list[DocumentChunkRow]:
    return [
        DocumentChunkRow(
            id=chunk.id,
            document_id=str(document_id),
            index=chunk.index,
            text=chunk.text,
            page=chunk.page,
            section=chunk.section,
        )
        for chunk in chunks
    ]


def _read_file(storage_path: str | None) -> bytes | None:
    if not storage_path:
        return None
    path = Path(storage_path)
    if not path.is_file():
        return None
    return path.read_bytes()


def _remove_file(storage_path: str | None) -> None:
    if not storage_path:
        return
    path = Path(storage_path)
    if path.is_file():
        path.unlink()


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _to_document(row: DocumentRow) -> Document:
    return Document(
        id=UUID(row.id),
        kind=DocumentKind(row.kind),
        filename=row.filename,
        title=row.title,
        mime=row.mime,
        size_bytes=row.size_bytes,
        status=DocumentStatus(row.status),
        error=row.error,
        case_id=UUID(row.case_id) if row.case_id else None,
        chunk_count=row.chunk_count,
        created_at=_as_utc(row.created_at),
    )


def _to_detail(row: DocumentRow) -> DocumentDetail:
    return DocumentDetail(
        **_to_document(row).model_dump(),
        text=row.text,
        page_count=row.page_count,
    )


def _to_chunk(row: DocumentChunkRow) -> Chunk:
    return Chunk(
        id=row.id,
        document_id=UUID(row.document_id),
        index=row.index,
        text=row.text,
        page=row.page,
        section=row.section,
    )
