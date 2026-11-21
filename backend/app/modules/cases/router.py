"""Endpointy wniosków (WS1).

Router tylko deleguje: walidacja i maszyna stanów mieszkają w `service.py`,
a trwałość w adapterze wybieranym przez kontener (`fake` albo `real`).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.contracts import (
    Case,
    CaseCreate,
    CaseDetail,
    CasePatch,
    CaseStatus,
    HistoryEntry,
    TransitionRequest,
)
from app.core import container
from app.modules.archive.service import index_closed_case
from app.modules.audit.service import (
    AuditAction,
    AuditEntity,
    AuditRecorder,
    audit_recorder,
    changed_fields,
)
from app.modules.cases.service import CaseService
from app.ports.cases import CaseRepositoryPort

router = APIRouter(tags=["cases"])


@router.get("", response_model=list[Case])
def list_cases(
    year: int | None = None,
    status: CaseStatus | None = None,
    q: str | None = None,
    sort: str = Query("deadline_asc", pattern="^(deadline|inflow)_(asc|desc)$"),
    repo: CaseRepositoryPort = Depends(container.get_cases),
) -> list[Case]:
    return CaseService(repo).list(year=year, status=status, q=q, sort=sort)


@router.get("/years", response_model=list[int])
def list_years(repo: CaseRepositoryPort = Depends(container.get_cases)) -> list[int]:
    return CaseService(repo).years()


@router.post("", response_model=Case, status_code=201)
def create_case(
    data: CaseCreate,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Case:
    case = CaseService(repo).create(data)
    audit.record(
        action=AuditAction.CASE_CREATED,
        entity_type=AuditEntity.CASE,
        entity_id=case.id,
        case_id=case.id,
        payload={
            "case_number": case.case_number,
            "subject": case.subject,
            "inflow_date": case.inflow_date,
        },
    )
    return case


@router.get("/{case_id}", response_model=CaseDetail)
def get_case(
    case_id: UUID, repo: CaseRepositoryPort = Depends(container.get_cases)
) -> CaseDetail:
    return CaseService(repo).get(case_id)


@router.patch("/{case_id}", response_model=Case)
def patch_case(
    case_id: UUID,
    patch: CasePatch,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Case:
    case = CaseService(repo).update(case_id, patch)
    audit.record(
        action=AuditAction.CASE_UPDATED,
        entity_type=AuditEntity.CASE,
        entity_id=case_id,
        case_id=case_id,
        payload=changed_fields(patch),
    )
    return case


@router.post("/{case_id}/transition", response_model=Case)
def transition_case(
    case_id: UUID,
    body: TransitionRequest,
    repo: CaseRepositoryPort = Depends(container.get_cases),
    audit: AuditRecorder = Depends(audit_recorder),
) -> Case:
    service = CaseService(repo)
    before = service.get(case_id)
    case = service.transition(case_id, body)
    audit.record(
        action=AuditAction.CASE_TRANSITIONED,
        entity_type=AuditEntity.CASE,
        entity_id=case_id,
        case_id=case_id,
        actor=body.actor,
        payload={"from": before.status.value, "to": case.status.value, "note": body.note},
    )
    # Zamknięcie sprawy wzbogaca archiwum — od tej chwili wniosek jest
    # znajdowalny w „Archiwum spraw” razem z gotową odpowiedzią (W8).
    if case.status is CaseStatus.ODPOWIEDZ_WYSLANA:
        index_closed_case(service.get(case_id))
    return case


@router.get("/{case_id}/history", response_model=list[HistoryEntry])
def case_history(
    case_id: UUID, repo: CaseRepositoryPort = Depends(container.get_cases)
) -> list[HistoryEntry]:
    return CaseService(repo).history(case_id)
