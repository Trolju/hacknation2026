"""Generator odpowiedzi oparty o model językowy (WS5).

Przepływ jednego projektu:

1. sprawa z `container.get_cases()`, sprawy zbliżone z `container.get_archive()`,
   przepisy z `fixtures/statutes/`, treść dokumentów sprawy z `container.get_documents()`,
2. prompt z sekcjami i **twardym** wymaganiem: każde twierdzenie merytoryczne
   musi nieść odnośnik do źródła,
3. `LLMPort.complete()`,
4. kontrola pokrycia: odnośniki do nieistniejących źródeł są usuwane, a zdania
   bez źródła trafiają do `unsupported` — nic nie jest usuwane po cichu.

Gdy model jest niedostępny (tryb offline, błąd serwera modelu, treść nie do
wykorzystania), projekt powstaje z szablonu, a `unsupported` mówi o tym wprost.
Urzędnik zawsze dostaje pismo, nigdy pusty ekran.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final
from uuid import UUID, uuid4

import structlog
from sqlalchemy import Engine

from app.contracts import (
    ApplyRequest,
    CaseDetail,
    Citation,
    DetectRequest,
    Draft,
    DraftPatch,
    DraftRequest,
)
from app.core import container
from app.core.clock import now, today
from app.core.errors import AppError, NotFound, OfflineViolation
from app.core.settings import settings
from app.modules.drafting import export as exporter
from app.modules.drafting.prompt import (
    SYSTEM_PROMPT,
    build_prompt,
    extract_refs,
    find_unsupported,
    is_usable,
    normalize_model_output,
    strip_invalid_refs,
)
from app.modules.drafting.repository import DraftRepository, DraftVersion
from app.modules.drafting.sources import Source, collect_sources
from app.modules.drafting.template import build_template, format_date_pl
from app.ports.anonymize import AnonymizerPort
from app.ports.archive import ArchiveSearchPort
from app.ports.cases import CaseRepositoryPort
from app.ports.documents import DocumentStorePort
from app.ports.inference import LLMPort

log = structlog.get_logger(__name__)

DEFAULT_ACTOR: Final[str] = "urzędnik"
TITLE_PREFIX: Final[str] = "Projekt odpowiedzi na wniosek"

OFFLINE_NOTE: Final[str] = (
    "Model językowy jest niedostępny w trybie offline — projekt przygotowano z szablonu. "
    "Sprawdź każde twierdzenie przed wysłaniem."
)
MODEL_ERROR_NOTE: Final[str] = (
    "Model językowy jest chwilowo niedostępny — projekt przygotowano z szablonu. "
    "Sprawdź każde twierdzenie przed wysłaniem."
)
UNUSABLE_NOTE: Final[str] = (
    "Model językowy zwrócił treść, której nie można wykorzystać w projekcie pisma — "
    "użyto szablonu. Sprawdź każde twierdzenie przed wysłaniem."
)


def _citations_for(body: str, sources: Sequence[Source]) -> list[Citation]:
    """Cytowania tylko dla źródeł faktycznie przywołanych w treści."""
    used = set(extract_refs(body))
    return [source.citation() for source in sources if source.ref in used]


def _change_note(before: Draft, after: Draft) -> str:
    """Krótki opis zmiany — „co” w historii wersji."""
    delta = len(after.body) - len(before.body)
    sign = "+" if delta >= 0 else "−"
    parts = [f"treść: {len(after.body)} znaków ({sign}{abs(delta)})"]
    if after.title != before.title:
        parts.append("tytuł zmieniony")
    return "; ".join(parts)


class LlmDrafting:
    """Implementacja `DraftingPort`: model językowy z degradacją do szablonu."""

    def __init__(
        self,
        *,
        engine: Engine | None = None,
        llm: LLMPort | None = None,
        cases: CaseRepositoryPort | None = None,
        archive: ArchiveSearchPort | None = None,
        documents: DocumentStorePort | None = None,
        anonymizer: AnonymizerPort | None = None,
        repository: DraftRepository | None = None,
    ) -> None:
        self._llm = llm
        self._cases = cases
        self._archive = archive
        self._documents = documents
        self._anonymizer = anonymizer
        self._repo = repository or DraftRepository(engine=engine)

    # ── zależności (leniwie, żeby kontener mógł podmienić dowolny moduł) ──
    @property
    def _llm_port(self) -> LLMPort:
        return self._llm or container.get_llm()

    @property
    def _cases_port(self) -> CaseRepositoryPort:
        return self._cases or container.get_cases()

    @property
    def _archive_port(self) -> ArchiveSearchPort:
        return self._archive or container.get_archive()

    @property
    def _documents_port(self) -> DocumentStorePort:
        return self._documents or container.get_documents()

    @property
    def _anonymizer_port(self) -> AnonymizerPort:
        return self._anonymizer or container.get_anonymizer()

    # ── generowanie ──
    def draft(self, req: DraftRequest) -> Draft:
        case = self._cases_port.get(req.case_id)
        sources = collect_sources(
            case,
            use_archive=req.use_archive,
            use_statutes=req.use_statutes,
            department_reply_ids=req.department_reply_ids,
            archive=self._archive_port,
            documents=self._documents_port,
        )
        prompt = build_prompt(case, sources, req)

        try:
            raw = self._llm_port.complete(
                prompt,
                system=SYSTEM_PROMPT,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
        except OfflineViolation:
            log.info("drafting_degraded", case_id=str(case.id), reason="offline")
            return self._degraded(case, sources, OFFLINE_NOTE)
        except Exception as exc:
            log.warning(
                "drafting_degraded",
                case_id=str(case.id),
                reason="model_error",
                error=type(exc).__name__,
            )
            return self._degraded(case, sources, MODEL_ERROR_NOTE)

        body = normalize_model_output(raw)
        if not is_usable(body):
            log.info("drafting_degraded", case_id=str(case.id), reason="unusable_output")
            return self._degraded(case, sources, UNUSABLE_NOTE)

        cleaned = strip_invalid_refs(body, {source.ref for source in sources})
        citations = _citations_for(cleaned, sources)
        unsupported = find_unsupported(cleaned, {citation.ref for citation in citations})
        log.info(
            "drafting_generated",
            case_id=str(case.id),
            citations=len(citations),
            unsupported=len(unsupported),
        )
        return self._persist(
            case,
            cleaned,
            citations,
            unsupported,
            action="generated",
            note="projekt z modelu językowego",
        )

    def _degraded(self, case: CaseDetail, sources: Sequence[Source], note: str) -> Draft:
        """Projekt z szablonu — gdy model nie dostarczył użytecznej treści."""
        body = build_template(case, sources)
        citations = _citations_for(body, sources)
        unsupported = [note, *find_unsupported(body, {c.ref for c in citations})]
        return self._persist(
            case,
            body,
            citations,
            unsupported,
            action="generated",
            note="projekt z szablonu",
        )

    def _persist(
        self,
        case: CaseDetail,
        body: str,
        citations: list[Citation],
        unsupported: list[str],
        *,
        action: str,
        note: str,
    ) -> Draft:
        existing = self._repo.get_by_case(case.id)
        stamp = now()
        draft = Draft(
            id=existing.id if existing else uuid4(),
            case_id=case.id,
            title=f"{TITLE_PREFIX} {case.case_number}",
            body=body,
            citations=citations,
            unsupported=unsupported,
            created_at=existing.created_at if existing else stamp,
            updated_at=stamp if existing else None,
        )
        return self._repo.save(draft, actor=DEFAULT_ACTOR, action=action, note=note)

    # ── odczyt i edycja ──
    def get(self, case_id: UUID) -> Draft:
        draft = self._repo.get_by_case(case_id)
        if draft is None:
            raise NotFound("Brak projektu odpowiedzi dla tego wniosku.")
        return draft

    def update(self, draft_id: UUID, patch: DraftPatch) -> Draft:
        draft = self._repo.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")
        updated = draft.model_copy(
            update={
                "body": patch.body,
                "title": patch.title or draft.title,
                "updated_at": now(),
            }
        )
        return self._repo.save(
            updated,
            actor=DEFAULT_ACTOR,
            action="edited",
            note=_change_note(draft, updated),
        )

    def history(self, draft_id: UUID) -> list[DraftVersion]:
        """Historia wersji — poza portem, używana przez testy i przyszły ekran."""
        return self._repo.history(draft_id)

    # ── eksport ──
    def export(self, draft_id: UUID, *, fmt: str, anonymized: bool) -> tuple[bytes, str]:
        draft = self._repo.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")

        title = draft.title
        body = draft.body
        citations = list(draft.citations)
        if anonymized:
            title, _ = self._anonymize(title)
            body, _ = self._anonymize(body)
            cleaned: list[Citation] = []
            for citation in citations:
                label, _ = self._anonymize(citation.label)
                excerpt, _ = self._anonymize(citation.excerpt)
                cleaned.append(
                    citation.model_copy(update={"label": label, "excerpt": excerpt})
                )
            citations = cleaned

        header = self._header_lines(draft)
        suffix = "anon" if anonymized else "projekt"
        stem = f"odpowiedz-{draft.case_id.hex[:8]}-{suffix}"

        if fmt == "docx":
            blob = exporter.render_docx(
                title=title, body=body, citations=citations, header_lines=header
            )
            return blob, f"{stem}.docx"
        if fmt == "pdf":
            blob = exporter.render_pdf(
                title=title, body=body, citations=citations, header_lines=header
            )
            return blob, f"{stem}.pdf"
        if fmt in ("md", "markdown"):
            blob = exporter.render_markdown(title=title, body=body, citations=citations)
            return blob, f"{stem}.md"
        raise NotFound(f"Nieobsługiwany format eksportu: {fmt}.")

    def redactions(self, draft_id: UUID) -> int:
        """Ile fragmentów usunęłaby anonimizacja — 0, gdy nie ma czego ukrywać."""
        draft = self._repo.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")
        total = self._anonymize(draft.title)[1] + self._anonymize(draft.body)[1]
        for citation in draft.citations:
            total += self._anonymize(citation.label)[1]
            total += self._anonymize(citation.excerpt)[1]
        return total

    def _header_lines(self, draft: Draft) -> list[str]:
        """Nagłówek pisma urzędowego: miejsce, data i znak sprawy."""
        try:
            case = self._cases_port.get(draft.case_id)
        except AppError:
            return []
        return [
            f"Bydgoszcz, dnia {format_date_pl(today())}",
            f"Znak sprawy: {case.case_number}",
        ]

    def _anonymize(self, text: str) -> tuple[str, int]:
        """Przepuszcza tekst przez anonimizator; zwraca (tekst, liczba trafień)."""
        if not text.strip():
            return text, 0
        anonymizer = self._anonymizer_port
        spans = anonymizer.detect(DetectRequest(text=text))
        if not spans:
            return text, 0
        return anonymizer.apply(ApplyRequest(text=text, spans=spans)).text, len(spans)
