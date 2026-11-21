"""Endpointy routingu wydziałowego (WS4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contracts import (
    Department,
    DepartmentSuggestion,
    GeneratedLetter,
    InquiryRequest,
    SuggestRequest,
)
from app.core import container
from app.ports.routing import DepartmentRouterPort

router = APIRouter(tags=["routing"])


@router.get("/departments", response_model=list[Department])
def departments(
    router_port: DepartmentRouterPort = Depends(container.get_routing),
) -> list[Department]:
    return router_port.departments()


@router.post("/suggest", response_model=list[DepartmentSuggestion])
def suggest(
    req: SuggestRequest, router_port: DepartmentRouterPort = Depends(container.get_routing)
) -> list[DepartmentSuggestion]:
    return router_port.suggest(req)


@router.post("/inquiry", response_model=GeneratedLetter)
def inquiry(
    req: InquiryRequest, router_port: DepartmentRouterPort = Depends(container.get_routing)
) -> GeneratedLetter:
    return router_port.inquiry(req)
