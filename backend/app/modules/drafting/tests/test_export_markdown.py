"""Eksport projektu — spójność formy odnośników między formatami.

P16 z raportu z testów na żywym Mistralu: DOCX i PDF zamieniały `[^n]` na
`[n]`, a Markdown zostawiał postać źródłową z caret. Urzędnik, który wkleja
treść z pliku `.md` do pisma, musiał te znaczniki usuwać ręcznie.
"""

from __future__ import annotations

from app.contracts import Citation
from app.modules.drafting.export import markers_to_plain, plain_text, render_markdown

BODY = (
    "## Podstawa prawna\n"
    "Zgodnie z ustawą (Dz. U. z 2023 r.) [^2]–[^13] oraz § 4 [^1].\n"
    "\n"
    "**Ważne** zdanie [^3]."
)

CITATION = Citation(
    ref=1,
    source_type="statute",
    source_id="zarzadzenie-412-2023#§ 4.",
    label="§ 4 zarządzenia nr 412/2023",
    excerpt="",
)


class TestMarkersToPlain:
    def test_zamienia_pojedynczy_znacznik(self) -> None:
        assert markers_to_plain("Zdanie [^1].") == "Zdanie [1]."

    def test_zamienia_zakres(self) -> None:
        assert markers_to_plain("Podstawa [^2]–[^13].") == "Podstawa [2]–[13]."

    def test_nie_rusza_zwyklego_nawiasu(self) -> None:
        assert markers_to_plain("Zobacz [1] i [2].") == "Zobacz [1] i [2]."

    def test_nie_rusza_pogrubienia(self) -> None:
        assert markers_to_plain("**Ważne** [^1].") == "**Ważne** [1]."


class TestPlainText:
    def test_usuwa_pogrubienie_i_caret(self) -> None:
        assert plain_text("**Ważne** zdanie [^1].") == "Ważne zdanie [1]."


class TestRenderMarkdown:
    def test_brak_caretow_w_tresci(self) -> None:
        text = render_markdown(title="Projekt", body=BODY, citations=[CITATION]).decode()

        assert "[^" not in text

    def test_odnosniki_w_formie_nawiasowej(self) -> None:
        text = render_markdown(title="Projekt", body=BODY, citations=[CITATION]).decode()

        assert "[2]–[13]" in text
        assert "§ 4 [1]." in text

    def test_naglowki_i_pogrubienia_zostaja_markdownem(self) -> None:
        """To plik do dalszej pracy, nie do druku — struktura ma zostać."""
        text = render_markdown(title="Projekt", body=BODY, citations=[CITATION]).decode()

        assert "## Podstawa prawna" in text
        assert "**Ważne**" in text

    def test_cytowania_na_koncu(self) -> None:
        text = render_markdown(title="Projekt", body=BODY, citations=[CITATION]).decode()

        assert "## Cytowania" in text
        assert "- [1] § 4 zarządzenia nr 412/2023" in text

    def test_bez_cytowan_nie_dopisuje_sekcji(self) -> None:
        text = render_markdown(title="Projekt", body=BODY, citations=[]).decode()

        assert "## Cytowania" not in text
