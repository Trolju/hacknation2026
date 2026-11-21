"""Endpointy generatora odpowiedzi (WS5)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.contracts import Draft, DraftPatch, DraftRequest
from app.core import container
from app.modules.audit.service import (
    AuditAction,
    AuditEntity,
    AuditRecorder,
    audit_recorder,
)
from app.ports.drafting import DraftingPort

router = APIRouter(tags=["drafting"])

_MEDIA = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "md": "text/markdown; charset=utf-8",
}


@router.post("/draft", response_model=Draft)
def create_draft(
    req: DraftRequest,
    service: DraftingPort = Depends(container.get_drafting),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Draft:
    draft = service.draft(req)
    audit.record(
        action=AuditAction.DRAFT_GENERATED,
        entity_type=AuditEntity.DRAFT,
        entity_id=draft.id,
        case_id=draft.case_id,
        payload={
            "citations": len(draft.citations),
            "unsupported": len(draft.unsupported),
        },
    )
    return draft


@router.get("/{case_id}", response_model=Draft)
def get_draft(
    case_id: UUID, service: DraftingPort = Depends(container.get_drafting)
) -> Draft:
    return service.get(case_id)


@router.patch("/{draft_id}", response_model=Draft)
def patch_draft(
    draft_id: UUID,
    patch: DraftPatch,
    service: DraftingPort = Depends(container.get_drafting),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Draft:
    draft = service.update(draft_id, patch)
    audit.record(
        action=AuditAction.DRAFT_SAVED,
        entity_type=AuditEntity.DRAFT,
        entity_id=draft.id,
        case_id=draft.case_id,
        payload={"title": draft.title, "body_length": len(draft.body)},
    )
    return draft


@router.get("/{draft_id}/export")
def export_draft(
    draft_id: UUID,
    fmt: str = Query("docx", pattern="^(docx|pdf|md)$"),
    anonymized: bool = False,
    service: DraftingPort = Depends(container.get_drafting),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Response:
    blob, filename = service.export(draft_id, fmt=fmt, anonymized=anonymized)
    redactions = service.redactions(draft_id) if anonymized else 0
    # Port nie zna odczytu po `draft_id`, więc wpis nie niesie `case_id` —
    # identyfikator projektu i nazwa pliku wystarczą, żeby odnaleźć zdarzenie.
    audit.record(
        action=AuditAction.DRAFT_EXPORTED,
        entity_type=AuditEntity.DRAFT,
        entity_id=draft_id,
        payload={
            "format": fmt,
            "anonymized": anonymized,
            "filename": filename,
            "redactions": redactions,
        },
    )
    return Response(
        content=blob,
        media_type=_MEDIA.get(fmt, "application/octet-stream"),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Redactions": str(redactions),
        },
    )
