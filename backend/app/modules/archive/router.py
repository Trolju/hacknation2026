"""Endpointy archiwum (WS3)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.contracts import ArchiveCase, SimilarCase, SimilarRequest
from app.core import container
from app.ports.archive import ArchiveSearchPort

router = APIRouter(tags=["archive"])


@router.post("/similar", response_model=list[SimilarCase])
def similar(
    req: SimilarRequest, search: ArchiveSearchPort = Depends(container.get_archive)
) -> list[SimilarCase]:
    return search.similar(req)


@router.get("/{archive_id}", response_model=ArchiveCase)
def get_archive_case(
    archive_id: str, search: ArchiveSearchPort = Depends(container.get_archive)
) -> ArchiveCase:
    return search.get(archive_id)
