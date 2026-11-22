"""Atrapa dokumentów — realne parsery PDF/DOCX, magazyn w pamięci."""

from __future__ import annotations

import builtins
import io
from pathlib import Path
from uuid import UUID, uuid4

from app.contracts import (
    Chunk,
    Document,
    DocumentDetail,
    DocumentKind,
    DocumentStatus,
)
from app.core.clock import now as clock_now
from app.core.errors import NotFound, UnsupportedMedia

_PDF = "application/pdf"
_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
_MIME = {
    ".pdf": _PDF,
    ".docx": _DOCX,
    ".txt": "text/plain",
    ".md": "text/markdown",
}

CHUNK_CHARS = 900
CHUNK_OVERLAP = 120


def _pdf_pages(blob: bytes) -> builtins.list[str]:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        return [(page.extract_text() or "").strip() for page in pdf.pages]


def _docx_pages(blob: bytes) -> builtins.list[str]:
    import docx

    document = docx.Document(io.BytesIO(blob))
    text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
    return [text.strip()]


class FakeDocumentParser:
    def parse(self, blob: bytes, filename: str) -> tuple[str, int]:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            pages = _pdf_pages(blob)
        elif suffix == ".docx":
            pages = _docx_pages(blob)
        elif suffix in (".txt", ".md"):
            pages = [blob.decode("utf-8", errors="replace").strip()]
        else:
            raise UnsupportedMedia(f"Nieobsługiwany format pliku: {suffix or 'brak'}.")
        text = "\n\n".join(p for p in pages if p)
        if not text:
            raise UnsupportedMedia("Dokument nie zawiera warstwy tekstowej.")
        return text, len(pages)

    def chunk(self, text: str, *, document_id: UUID) -> builtins.list[Chunk]:
        chunks: list[Chunk] = []
        start = 0
        index = 0
        while start < len(text):
            end = min(start + CHUNK_CHARS, len(text))
            if end < len(text):
                cut = text.rfind("\n", start, end)
                if cut > start + CHUNK_CHARS // 2:
                    end = cut
            body = text[start:end].strip()
            if body:
                chunks.append(
                    Chunk(
                        id=f"{document_id}:{index}",
                        document_id=document_id,
                        index=index,
                        text=body,
                    )
                )
                index += 1
            if end >= len(text):
                break
            start = max(end - CHUNK_OVERLAP, start + 1)
        return chunks


class FakeDocumentStore:
    def __init__(self, parser: FakeDocumentParser | None = None) -> None:
        self._parser = parser or FakeDocumentParser()
        self._docs: dict[UUID, DocumentDetail] = {}
        self._chunks: dict[UUID, list[Chunk]] = {}

    def list(
        self, *, kind: DocumentKind | None = None, case_id: UUID | None = None
    ) -> builtins.list[Document]:
        rows = list(self._docs.values())
        if kind is not None:
            rows = [d for d in rows if d.kind == kind]
        if case_id is not None:
            rows = [d for d in rows if d.case_id == case_id]
        rows.sort(key=lambda d: d.created_at, reverse=True)
        return [Document(**d.model_dump(exclude={"text", "page_count"})) for d in rows]

    def get(self, document_id: UUID) -> DocumentDetail:
        doc = self._docs.get(document_id)
        if doc is None:
            raise NotFound("Nie znaleziono dokumentu.")
        return doc

    def create(
        self,
        *,
        blob: bytes,
        filename: str,
        kind: DocumentKind,
        case_id: UUID | None = None,
        title: str | None = None,
    ) -> Document:
        doc_id = uuid4()
        mime = _MIME.get(Path(filename).suffix.lower(), "application/octet-stream")
        try:
            text, page_count = self._parser.parse(blob, filename)
            chunks = self._parser.chunk(text, document_id=doc_id)
            status = DocumentStatus.INDEXED
            error = None
        except UnsupportedMedia as exc:
            text, page_count, chunks = "", 0, []
            status = DocumentStatus.FAILED
            error = exc.message
        detail = DocumentDetail(
            id=doc_id,
            kind=kind,
            filename=filename,
            title=title or Path(filename).stem,
            mime=mime,
            size_bytes=len(blob),
            status=status,
            error=error,
            case_id=case_id,
            chunk_count=len(chunks),
            created_at=clock_now(),
            text=text,
            page_count=page_count,
        )
        self._docs[doc_id] = detail
        self._chunks[doc_id] = chunks
        return Document(**detail.model_dump(exclude={"text", "page_count"}))

    def delete(self, document_id: UUID) -> None:
        if document_id not in self._docs:
            raise NotFound("Nie znaleziono dokumentu.")
        self._docs.pop(document_id)
        self._chunks.pop(document_id, None)

    def chunks(self, document_id: UUID) -> builtins.list[Chunk]:
        if document_id not in self._docs:
            raise NotFound("Nie znaleziono dokumentu.")
        return list(self._chunks.get(document_id, []))

    def reindex(self, document_id: UUID) -> Document:
        doc = self.get(document_id)
        chunks = self._parser.chunk(doc.text, document_id=document_id)
        self._chunks[document_id] = chunks
        updated = doc.model_copy(
            update={"chunk_count": len(chunks), "status": DocumentStatus.INDEXED}
        )
        self._docs[document_id] = updated
        return Document(**updated.model_dump(exclude={"text", "page_count"}))
