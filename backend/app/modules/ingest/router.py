"""Endpointy dokumentów (WS2)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.contracts import Chunk, Document, DocumentDetail, DocumentKind
from app.core import container
from app.core.errors import PayloadTooLarge
from app.core.settings import settings
from app.modules.audit.service import (
    AuditAction,
    AuditEntity,
    AuditRecorder,
    audit_recorder,
)
from app.ports.documents import DocumentStorePort

PREFIX = "documents"

router = APIRouter(tags=["documents"])


@router.get("", response_model=list[Document])
def list_documents(
    kind: DocumentKind | None = None,
    case_id: UUID | None = None,
    store: DocumentStorePort = Depends(container.get_documents),
) -> list[Document]:
    return store.list(kind=kind, case_id=case_id)


@router.post("", response_model=Document, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    kind: DocumentKind = Form(DocumentKind.INNE),
    case_id: UUID | None = Form(None),
    title: str | None = Form(None),
    store: DocumentStorePort = Depends(container.get_documents),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Document:
    blob = await file.read()
    if len(blob) > settings.max_upload_bytes:
        raise PayloadTooLarge(
            f"Plik przekracza limit {settings.max_upload_bytes // (1024 * 1024)} MB."
        )
    document = store.create(
        blob=blob,
        filename=file.filename or "plik",
        kind=kind,
        case_id=case_id,
        title=title,
    )
    audit.record(
        action=AuditAction.DOCUMENT_UPLOADED,
        entity_type=AuditEntity.DOCUMENT,
        entity_id=document.id,
        case_id=case_id,
        payload={
            "filename": document.filename,
            "kind": document.kind.value,
            "size_bytes": document.size_bytes,
            "status": document.status.value,
        },
    )
    return document


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: UUID, store: DocumentStorePort = Depends(container.get_documents)
) -> DocumentDetail:
    return store.get(document_id)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    store: DocumentStorePort = Depends(container.get_documents),
    audit: AuditRecorder = Depends(audit_recorder),
) -> None:
    document = store.get(document_id)
    store.delete(document_id)
    audit.record(
        action=AuditAction.DOCUMENT_DELETED,
        entity_type=AuditEntity.DOCUMENT,
        entity_id=document_id,
        case_id=document.case_id,
        payload={"filename": document.filename, "kind": document.kind.value},
    )


@router.get("/{document_id}/chunks", response_model=list[Chunk])
def document_chunks(
    document_id: UUID, store: DocumentStorePort = Depends(container.get_documents)
) -> list[Chunk]:
    return store.chunks(document_id)


@router.post("/{document_id}/reindex", response_model=Document)
def reindex_document(
    document_id: UUID, store: DocumentStorePort = Depends(container.get_documents)
) -> Document:
    return store.reindex(document_id)
