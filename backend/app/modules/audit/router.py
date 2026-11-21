"""Endpointy dziennika audytu (WS8)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.contracts import AuditEntry
from app.core import container
from app.ports.audit import AuditPort

router = APIRouter(tags=["audit"])


@router.get("", response_model=list[AuditEntry])
def list_entries(
    case_id: UUID | None = None,
    limit: int = Query(100, ge=1, le=500),
    audit: AuditPort = Depends(container.get_audit),
) -> list[AuditEntry]:
    return audit.list(case_id=case_id, limit=limit)
