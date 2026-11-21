"""Porty dokumentów (WS2)."""

from __future__ import annotations

import builtins
from typing import Protocol
from uuid import UUID

from app.contracts import Chunk, Document, DocumentDetail, DocumentKind


class ParsedDocument(Protocol):
    text: str
    page_count: int
    chunks: list[Chunk]


class DocumentParserPort(Protocol):
    def parse(self, blob: bytes, filename: str) -> tuple[str, int]:
        """Zwraca (tekst, liczba_stron). Rzuca UnsupportedMedia / ValidationFailed."""
        ...

    def chunk(self, text: str, *, document_id: UUID) -> builtins.list[Chunk]: ...


class DocumentStorePort(Protocol):
    def list(
        self, *, kind: DocumentKind | None = None, case_id: UUID | None = None
    ) -> builtins.list[Document]: ...

    def get(self, document_id: UUID) -> DocumentDetail: ...

    def create(
        self,
        *,
        blob: bytes,
        filename: str,
        kind: DocumentKind,
        case_id: UUID | None = None,
        title: str | None = None,
    ) -> Document: ...

    def delete(self, document_id: UUID) -> None: ...

    def chunks(self, document_id: UUID) -> builtins.list[Chunk]: ...

    def reindex(self, document_id: UUID) -> Document: ...
