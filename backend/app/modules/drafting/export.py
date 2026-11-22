"""Eksport projektu odpowiedzi do DOCX, PDF i Markdown.

Eksport zachowuje strukturę pisma urzędowego: nagłówek (miejsce, data, znak
sprawy), tytuł, treść z nagłówkami i listami oraz listę cytowań na końcu.
Odnośniki `[^n]` w treści są zamieniane na `[n]` — w DOCX w indeksie górnym,
żeby nie rozbijały składu akapitu.
"""

from __future__ import annotations

import io
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.contracts import Citation
from app.core.errors import NotFound

BlockKind = Literal["heading", "paragraph", "bullet", "numbered"]

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^[-*+]\s+(.*)$")
_NUMBERED = re.compile(r"^\d+[.)]\s+(.*)$")
_INLINE = re.compile(r"(\*\*[^*]+\*\*|\[\^\d+\])")
_MARKER = re.compile(r"\[\^(\d+)\]")

_FONT_CANDIDATES: tuple[tuple[str, str], ...] = (
    (
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ),
)


@dataclass(frozen=True)
class Block:
    """Akapit treści po rozbiorze Markdownu."""

    kind: BlockKind
    text: str
    level: int = 0


def parse_blocks(markdown: str) -> list[Block]:
    """Zamienia Markdown projektu na akapity zrozumiałe dla eksporterów."""
    blocks: list[Block] = []
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = _HEADING.match(line)
        if heading:
            blocks.append(Block("heading", heading.group(2).strip(), len(heading.group(1))))
            continue
        bullet = _BULLET.match(line)
        if bullet:
            blocks.append(Block("bullet", bullet.group(1).strip()))
            continue
        numbered = _NUMBERED.match(line)
        if numbered:
            blocks.append(Block("numbered", numbered.group(1).strip()))
            continue
        blocks.append(Block("paragraph", line))
    return blocks


def markers_to_plain(text: str) -> str:
    """`[^n]` → `[n]` — forma czytelna w wydruku i w Markdownie.

    Znacznik `[^n]` to zapis źródłowy projektu. W gotowym piśmie odnośnik
    stoi w nawiasie kwadratowym, tak samo we wszystkich trzech formatach
    eksportu — bez tego Markdown zostawiał caret, którego DOCX i PDF nie mają.
    """
    return _MARKER.sub(lambda match: f"[{match.group(1)}]", text)


def plain_text(text: str) -> str:
    """Treść bez znaczników Markdownu — do PDF i podglądu."""
    return markers_to_plain(text.replace("**", ""))


def _citation_line(citation: Citation) -> str:
    excerpt = citation.excerpt.strip()
    if excerpt:
        return f"[{citation.ref}] {citation.label} — {excerpt}"
    return f"[{citation.ref}] {citation.label}"


# ─────────────────────────────────── DOCX ──────────────────────────────────
def _add_runs(paragraph: Any, text: str) -> None:
    """Wstawia tekst z pogrubieniami i odnośnikami w indeksie górnym."""
    for token in _INLINE.split(text):
        if not token:
            continue
        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif _MARKER.fullmatch(token):
            run = paragraph.add_run(f"[{token[2:-1]}]")
            run.font.superscript = True
        else:
            paragraph.add_run(token)


def render_docx(
    *,
    title: str,
    body: str,
    citations: Sequence[Citation],
    header_lines: Sequence[str] = (),
) -> bytes:
    """Projekt odpowiedzi jako plik DOCX."""
    import docx

    document = docx.Document()
    for line in header_lines:
        document.add_paragraph(line)
    document.add_heading(title, level=1)

    for block in parse_blocks(body):
        if block.kind == "heading":
            document.add_heading(plain_text(block.text), level=min(block.level, 4))
            continue
        style = "List Bullet" if block.kind == "bullet" else None
        paragraph = document.add_paragraph(style=style)
        _add_runs(paragraph, block.text)

    if citations:
        document.add_heading("Cytowania", level=2)
        for citation in citations:
            document.add_paragraph(_citation_line(citation))

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# ──────────────────────────────────── PDF ──────────────────────────────────
def _font_paths() -> tuple[str, str] | None:
    for regular, bold in _FONT_CANDIDATES:
        if Path(regular).exists() and Path(bold).exists():
            return regular, bold
    return None


def render_pdf(
    *,
    title: str,
    body: str,
    citations: Sequence[Citation],
    header_lines: Sequence[str] = (),
) -> bytes:
    """Projekt odpowiedzi jako plik PDF (czcionka DejaVu — polskie znaki)."""
    from fpdf import FPDF

    fonts = _font_paths()
    if fonts is None:
        raise NotFound("Brak fontu DejaVu — eksport PDF niedostępny.")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.add_font("DejaVu", fname=fonts[0])
    pdf.add_font("DejaVu", style="B", fname=fonts[1])

    def write(text: str, size: int, *, bold: bool = False, height: float = 6.0) -> None:
        pdf.set_font("DejaVu", "B" if bold else "", size=size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, height, text, new_x="LMARGIN", new_y="NEXT")

    for line in header_lines:
        write(plain_text(line), 10)
    if header_lines:
        pdf.ln(2)

    write(plain_text(title), 15, bold=True)
    pdf.ln(3)

    for block in parse_blocks(body):
        if block.kind == "heading":
            pdf.ln(2)
            write(plain_text(block.text), 12, bold=True)
            continue
        prefix = "- " if block.kind == "bullet" else ""
        write(f"{prefix}{plain_text(block.text)}", 11)

    if citations:
        pdf.ln(3)
        write("Cytowania", 12, bold=True)
        for citation in citations:
            write(plain_text(_citation_line(citation)), 9, height=5.0)

    return bytes(pdf.output())


# ───────────────────────────────── Markdown ────────────────────────────────
def render_markdown(
    *, title: str, body: str, citations: Sequence[Citation]
) -> bytes:
    """Projekt odpowiedzi jako Markdown — wersja robocza do wklejenia dalej.

    Odnośniki idą w formie `[n]`, tak jak w DOCX i PDF. Nagłówki i pogrubienia
    zostają Markdownem, bo to plik do dalszej pracy, nie do druku.
    """
    parts = [f"# {title}", "", markers_to_plain(body.strip())]
    if citations:
        parts += ["", "## Cytowania", ""]
        parts += [f"- {_citation_line(citation)}" for citation in citations]
    return ("\n".join(parts) + "\n").encode("utf-8")
