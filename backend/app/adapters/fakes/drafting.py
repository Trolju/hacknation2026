"""Atrapa generatora odpowiedzi — szablon oparty o archiwum i przepisy."""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.contracts import Citation, Draft, DraftPatch, DraftRequest
from app.core.clock import now as clock_now
from app.core.errors import NotFound

if TYPE_CHECKING:
    from app.modules.drafting.sources import Source

_LEGAL = (
    "Zgodnie z art. 13 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do "
    "informacji publicznej (Dz.U. z 2022 r. poz. 902 ze zm.) informacja publiczna, "
    "która nie została udostępniona w Biuletynie Informacji Publicznej, jest "
    "udostępniana na wniosek. Zgodnie z art. 13 ust. 2 tej ustawy udostępnienie "
    "informacji następuje w terminie 14 dni od dnia złożenia wniosku."
)

_CLOSING = (
    "Jednocześnie informuję o możliwości wniesienia skargi do Wojewódzkiego Sądu "
    "Administracyjnego w Bydgoszczy z powodu bezczynności organu, na zasadach "
    "określonych w art. 21 ustawy o dostępie do informacji publicznej.\n\n"
    "Z upoważnienia Prezydenta Miasta Bydgoszczy"
)


def _from_document(source_id: str) -> bool:
    """Czy źródło pochodzi z wgranego dokumentu, a nie z `fixtures/statutes/`."""
    head = source_id.split("#", 1)[0]
    try:
        UUID(head)
    except ValueError:
        return False
    return True


class FakeDrafting:
    def __init__(self) -> None:
        self._drafts: dict[UUID, Draft] = {}
        self._by_case: dict[UUID, UUID] = {}

    def _uploaded_statutes(self) -> list[Source]:
        """Przepisy z wgranych ustaw i zarządzeń (W8).

        Atrapa ma zaszyty szablon podstawy prawnej (art. 13 UDIP), ale wgrany
        akt musi być widoczny także w trybie demo — inaczej urzędnik wgrywa
        ustawę i nic się nie dzieje. Bierzemy wyłącznie źródła pochodzące
        z dokumentów: ich `source_id` zaczyna się od UUID dokumentu, a przepisy
        z `fixtures/` od sługu aktu (`udip`, `kpa`, `zarzadzenie-412-2023`).
        """
        from app.core import container
        from app.modules.drafting.sources import statute_sources

        try:
            sources = statute_sources(container.get_documents())
        except Exception:  # magazyn dokumentów niedostępny — zostaje szablon
            return []
        return [source for source in sources if _from_document(source.source_id)]

    def draft(self, req: DraftRequest) -> Draft:
        existing = self._by_case.get(req.case_id)
        if existing is not None:
            return self._drafts[existing]

        citations: list[Citation] = []
        if req.use_statutes:
            citations.append(
                Citation(
                    ref=1,
                    source_type="statute",
                    source_id="udip",
                    label="art. 13 ust. 1 i 2 ustawy o dostępie do informacji publicznej",
                    excerpt=_LEGAL[:200],
                )
            )

        uploaded = self._uploaded_statutes() if req.use_statutes else []
        legal_extra: list[str] = []
        for source in uploaded:
            ref = len(citations) + 1
            citations.append(
                Citation(
                    ref=ref,
                    source_type="statute",
                    source_id=source.source_id,
                    label=source.label,
                    excerpt=source.excerpt,
                )
            )
            legal_extra.append(f"{source.text.strip()} [^{ref}]")

        body_parts = [
            "## Podstawa prawna",
            "",
            _LEGAL if req.use_statutes else "Podstawa prawna zostanie uzupełniona.",
        ]
        if legal_extra:
            body_parts += ["", "\n\n".join(legal_extra)]
        body_parts += [
            "",
            "## Odpowiedź",
            "",
            "W odpowiedzi na wniosek o udostępnienie informacji publicznej "
            "uprzejmie informuję, co następuje.",
        ]

        if req.use_archive:
            body_parts += [
                "",
                "## Rozstrzygnięcia w sprawach zbliżonych",
                "",
                "W analogicznych sprawach organ rozstrzygał w sposób jednolity; "
                "wcześniejsze rozstrzygnięcia znajdują się w archiwum spraw.",
            ]

        if req.department_reply_ids:
            body_parts += [
                "",
                "## Stanowiska komórek organizacyjnych",
                "",
                f"Uwzględniono {len(req.department_reply_ids)} odpowiedzi komórek.",
            ]

        body_parts += ["", "## Pouczenie", "", _CLOSING]

        stamp = clock_now()
        draft = Draft(
            id=uuid4(),
            case_id=req.case_id,
            title="Projekt odpowiedzi na wniosek",
            body="\n".join(body_parts),
            citations=citations,
            unsupported=[],
            created_at=stamp,
            updated_at=None,
        )
        self._drafts[draft.id] = draft
        self._by_case[req.case_id] = draft.id
        return draft

    def get(self, case_id: UUID) -> Draft:
        draft_id = self._by_case.get(case_id)
        if draft_id is None:
            raise NotFound("Brak projektu odpowiedzi dla tego wniosku.")
        return self._drafts[draft_id]

    def update(self, draft_id: UUID, patch: DraftPatch) -> Draft:
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")
        updated = draft.model_copy(
            update={
                "body": patch.body,
                "title": patch.title or draft.title,
                "updated_at": clock_now(),
            }
        )
        self._drafts[draft_id] = updated
        return updated

    def export(self, draft_id: UUID, *, fmt: str, anonymized: bool) -> tuple[bytes, str]:
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")
        if anonymized:
            draft = self._anonymized_copy(draft)
        suffix = "anon" if anonymized else "projekt"
        stem = f"odpowiedz-{draft.case_id.hex[:8]}-{suffix}"
        if fmt == "docx":
            return _docx(draft), f"{stem}.docx"
        if fmt == "pdf":
            return _pdf(draft), f"{stem}.pdf"
        if fmt in ("md", "markdown"):
            return draft.body.encode("utf-8"), f"{stem}.md"
        raise NotFound(f"Nieobsługiwany format eksportu: {fmt}.")

    def redactions(self, draft_id: UUID) -> int:
        """Ile fragmentów usunęłaby anonimizacja — 0, gdy nie ma czego ukrywać."""
        draft = self._drafts.get(draft_id)
        if draft is None:
            raise NotFound("Nie znaleziono projektu odpowiedzi.")
        total = self._anonymize(draft.title)[1] + self._anonymize(draft.body)[1]
        for citation in draft.citations:
            total += self._anonymize(citation.label)[1]
            total += self._anonymize(citation.excerpt)[1]
        return total

    def _anonymize(self, text: str) -> tuple[str, int]:
        """Przepuszcza tekst przez anonimizator; zwraca (tekst, liczba trafień)."""
        if not text.strip():
            return text, 0
        from app.contracts import ApplyRequest, DetectRequest
        from app.core import container

        anonymizer = container.get_anonymizer()
        spans = anonymizer.detect(DetectRequest(text=text))
        if not spans:
            return text, 0
        return anonymizer.apply(ApplyRequest(text=text, spans=spans)).text, len(spans)

    def _anonymized_copy(self, draft: Draft) -> Draft:
        title, _ = self._anonymize(draft.title)
        body, _ = self._anonymize(draft.body)
        citations = []
        for citation in draft.citations:
            label, _ = self._anonymize(citation.label)
            excerpt, _ = self._anonymize(citation.excerpt)
            citations.append(
                citation.model_copy(update={"label": label, "excerpt": excerpt})
            )
        return draft.model_copy(
            update={"title": title, "body": body, "citations": citations}
        )


def _docx(draft: Draft) -> bytes:
    import docx

    document = docx.Document()
    document.add_heading(draft.title, level=1)
    for line in draft.body.splitlines():
        if line.startswith("## "):
            document.add_heading(line[3:].strip(), level=2)
        elif line.strip():
            document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


_FONT_CANDIDATES = (
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


def _pdf(draft: Draft) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    for candidate in _FONT_CANDIDATES:
        if Path(candidate).exists():
            pdf.add_font("DejaVu", fname=candidate)
            break
    else:
        raise NotFound("Brak fontu DejaVu — eksport PDF niedostępny.")

    def write(text: str, size: int) -> None:
        pdf.set_font("DejaVu", size=size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, 6, text, new_x="LMARGIN", new_y="NEXT")

    write(draft.title, 14)
    pdf.ln(3)
    for line in draft.body.splitlines():
        if line.startswith("## "):
            pdf.ln(2)
            write(line[3:].strip(), 12)
        elif line.strip():
            write(line, 11)
    return bytes(pdf.output())
