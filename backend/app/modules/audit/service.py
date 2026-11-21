"""Zapis zdarzeń do dziennika audytu (WS8).

Jedno miejsce, w którym moduły zgłaszają operacje zapisu. Router nie zna
adaptera — dostaje port przez `Depends(container.get_audit)` i przekazuje go
tutaj. Dzięki temu dziennik działa identycznie na atrapie i na SQLite.

Wzorzec użycia w routerze innego modułu:

    from app.modules.audit.service import AuditAction, AuditEntity, audit_recorder

    @router.post("", response_model=Case, status_code=201)
    def create_case(
        data: CaseCreate,
        repo: CaseRepositoryPort = Depends(container.get_cases),
        audit: AuditRecorder = Depends(audit_recorder),
    ) -> Case:
        case = repo.create(data)
        audit.record(
            action=AuditAction.CASE_CREATED,
            entity_type=AuditEntity.CASE,
            entity_id=case.id,
            case_id=case.id,
            payload={"case_number": case.case_number, "subject": case.subject},
        )
        return case

Zasada: dziennik nie może przewrócić operacji biznesowej. Błąd zapisu jest
logowany jako ostrzeżenie i połykany — urzędnik nie traci pracy z powodu
zablokowanej bazy audytu. Świadoma decyzja: audyt jest pomocniczy wobec
podstawowego przepływu.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

import structlog
from fastapi import Depends
from pydantic import BaseModel

from app.core import container
from app.ports.audit import AuditPort

log = structlog.get_logger(__name__)

DEFAULT_ACTOR = "urzędnik"


class AuditAction(StrEnum):
    """Nazwy akcji w dzienniku. Format `obiekt.czynność`, po angielsku."""

    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_TRANSITIONED = "case.transitioned"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    DRAFT_GENERATED = "draft.generated"
    DRAFT_SAVED = "draft.saved"
    DRAFT_EXPORTED = "draft.exported"


class AuditEntity(StrEnum):
    """Typy obiektów, których dotyczą zdarzenia."""

    CASE = "case"
    DOCUMENT = "document"
    DRAFT = "draft"


def record(
    audit: AuditPort,
    *,
    action: str,
    entity_type: str,
    entity_id: str | UUID,
    case_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
    actor: str = DEFAULT_ACTOR,
) -> None:
    """Dopisuje zdarzenie do dziennika.

    Nigdy nie rzuca wyjątku — błąd zapisu trafia do logu jako ostrzeżenie.
    """
    try:
        audit.record(
            actor=actor,
            action=str(action),
            entity_type=str(entity_type),
            entity_id=str(entity_id),
            case_id=case_id,
            payload=payload or {},
        )
    except Exception as exc:  # noqa: BLE001 — dziennik nie może przerwać operacji
        log.warning(
            "audit_record_failed",
            action=str(action),
            entity_type=str(entity_type),
            entity_id=str(entity_id),
            error=type(exc).__name__,
        )


def changed_fields(patch: BaseModel) -> dict[str, Any]:
    """Zwraca tylko pola faktycznie podane w żądaniu PATCH.

    Dzięki temu wpis audytu mówi, co urzędnik zmienił, a nie jakie były
    wartości domyślne DTO.
    """
    return patch.model_dump(exclude_unset=True, exclude_none=True, mode="json")


class AuditRecorder:
    """Cienka otoczka nad portem, wstrzykiwana do routerów przez `Depends`."""

    def __init__(self, audit: AuditPort) -> None:
        self._audit = audit

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: str | UUID,
        case_id: UUID | None = None,
        payload: dict[str, Any] | None = None,
        actor: str = DEFAULT_ACTOR,
    ) -> None:
        record(
            self._audit,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            case_id=case_id,
            payload=payload,
            actor=actor,
        )


def audit_recorder(audit: AuditPort = Depends(container.get_audit)) -> AuditRecorder:
    """Zależność FastAPI: `audit: AuditRecorder = Depends(audit_recorder)`."""
    return AuditRecorder(audit)
