"""Indeksowanie zamkniętych wniosków w archiwum (W8).

Archiwum dostarczone w `fixtures/` jest zbiorem historycznym i nigdy się nie
zmienia. Żeby wymaganie „uczenie się na bazie wprowadzanych danych" było
spełnione, każdy wniosek, który przechodzi w stan `odpowiedz_wyslana`, trafia
do archiwum jako nowa sprawa — z tematem, treścią i gotową odpowiedzią.

Dzięki temu urzędnik, który w przyszłym roku dostanie podobny wniosek, znajdzie
w archiwum także sprawy załatwione przez siebie, a nie tylko te z materiałów
konkursowych.
"""

from __future__ import annotations

import contextlib

import structlog

from app.contracts import ArchiveCase, CaseDetail, CaseStatus
from app.core.errors import AppError
from app.ports.archive import ArchiveSearchPort
from app.ports.drafting import DraftingPort

log = structlog.get_logger(__name__)

#: Ile znaków odpowiedzi trafia do archiwum. Dłuższe teksty nie poprawiają
#: wyszukiwania, a rozdymają tabelę i indeks.
MAX_RESPONSE_CHARS = 4000


def archive_entry(case: CaseDetail, *, response_text: str = "") -> ArchiveCase:
    """Buduje wpis archiwalny z zamkniętego wniosku.

    `request_text` bierze notatki sprawy, jeśli są — zawierają treść wniosku
    albo streszczenie ustaleń. Bez notatek zostaje temat, który i tak jest
    indeksowany z podwyższoną wagą.
    """
    request_text = (case.notes or "").strip() or case.subject
    return ArchiveCase(
        archive_id="",
        case_number=case.case_number,
        subject=case.subject,
        year=case.year,
        request_text=request_text,
        response_text=response_text[:MAX_RESPONSE_CHARS],
        departments=list(case.department_ids),
    )


class ArchiveIndexer:
    """Dopisuje zamknięte wnioski do archiwum — najlepszym wysiłkiem."""

    def __init__(self, archive: ArchiveSearchPort, drafting: DraftingPort | None = None) -> None:
        self._archive = archive
        self._drafting = drafting

    def _response_text(self, case: CaseDetail) -> str:
        """Treść odpowiedzi z projektu pisma, jeśli taki istnieje."""
        if self._drafting is None:
            return ""
        try:
            draft = self._drafting.get(case.id)
        except AppError:
            return ""
        except Exception as exc:  # generator niedostępny — wpis bez odpowiedzi
            log.warning("archive_draft_unavailable", error=str(exc), case_id=str(case.id))
            return ""
        return draft.body

    def index(self, case: CaseDetail) -> str | None:
        """Indeksuje sprawę, jeśli jest zamknięta. Zwraca `archive_id` albo `None`.

        Wywołanie nigdy nie przerywa przejścia stanu: gdy archiwum zawiedzie,
        wniosek i tak zostaje zamknięty, a w logu pojawia się ostrzeżenie.
        """
        if case.status is not CaseStatus.ODPOWIEDZ_WYSLANA:
            return None
        entry = archive_entry(case, response_text=self._response_text(case))
        try:
            archive_id = self._archive.add(entry)
        except Exception as exc:
            log.warning(
                "archive_index_failed", error=str(exc), case_number=case.case_number
            )
            return None
        log.info(
            "archive_indexed",
            archive_id=archive_id,
            case_number=case.case_number,
        )
        return archive_id


def index_closed_case(case: CaseDetail) -> str | None:
    """Skrót dla routera: bierze adaptery z kontenera i indeksuje sprawę."""
    from app.core import container

    drafting: DraftingPort | None = None
    with contextlib.suppress(Exception):
        drafting = container.get_drafting()
    return ArchiveIndexer(container.get_archive(), drafting).index(case)
