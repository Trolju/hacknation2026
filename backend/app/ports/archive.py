"""Port wyszukiwania archiwalnego (WS3)."""

from __future__ import annotations

from typing import Protocol

from app.contracts import ArchiveCase, SimilarCase, SimilarRequest


class ArchiveSearchPort(Protocol):
    def similar(self, req: SimilarRequest) -> list[SimilarCase]: ...

    def get(self, archive_id: str) -> ArchiveCase: ...

    def size(self) -> int: ...

    def add(self, case: ArchiveCase) -> str:
        """Dopisuje sprawę do archiwum i zwraca jej identyfikator.

        Wywoływane, gdy wniosek przechodzi w stan `odpowiedz_wyslana` — dzięki
        temu archiwum rośnie wraz z pracą urzędu (W8), zamiast być zamrożonym
        zbiorem z `fixtures/`.

        Operacja jest idempotentna względem `case_number`: powtórne dodanie tej
        samej sprawy zwraca istniejący identyfikator i nie tworzy duplikatu.
        Pusty `archive_id` w argumencie oznacza „przydziel nowy”.
        """
        ...
