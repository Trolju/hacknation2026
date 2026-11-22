"""Normalizacja odpowiedzi modelu — format odnośników i definicje przypisów.

Dwa defekty z raportu z testów na żywym Mistralu:

* P1 — model pisze `[1]`, a nie `[^1]`, więc `is_usable` odrzucał poprawną
  treść i 20% projektów po cichu schodziło do szablonu,
* P3 — model dokleja na końcu blok definicji przypisów, który trafiał do
  eksportu DOCX i PDF jako zwykły akapit pisma.
"""

from __future__ import annotations

from app.modules.drafting.prompt import (
    find_unsupported,
    is_usable,
    normalize_model_output,
)

#: Odpowiedź w formacie, jaki realnie zwracał `mistral-small-latest` — bez
#: bloku definicji. To ten wariant przepadał w `is_usable` (P1).
MODEL_OUTPUT_PLAIN = """## Podstawa prawna

Zgodnie z art. 13 ust. 1 ustawy o dostępie do informacji publicznej udostępnianie
informacji następuje bez zbędnej zwłoki, nie później niż w terminie 14 dni [1].
Informacja publiczna nieudostępniona w BIP jest udostępniana na wniosek [2].

## Odpowiedź

Wynagrodzenia pracowników samorządowych stanowią informację publiczną [3].
"""

#: Ten sam tekst z doklejonym blokiem definicji (P3).
MODEL_OUTPUT = (
    MODEL_OUTPUT_PLAIN
    + """
[^1]: art. 13 ust. 1 ustawy o dostępie do informacji publicznej
[^2]: art. 10 ust. 1 ustawy o dostępie do informacji publicznej
[^3]: art. 5 ust. 2 ustawy o dostępie do informacji publicznej
"""
)


class TestPlainRefs:
    """P1 — `[n]` zamieniamy na `[^n]`."""

    def test_zamienia_zwykly_odnosnik(self) -> None:
        assert normalize_model_output("Zdanie [1] dalej.") == "Zdanie [^1] dalej."

    def test_zamienia_kilka_odnosnikow(self) -> None:
        assert normalize_model_output("A [1] B [2] C [12]") == "A [^1] B [^2] C [^12]"

    def test_nie_rusza_poprawnego_odnosnika(self) -> None:
        assert normalize_model_output("Zdanie [^1] dalej.") == "Zdanie [^1] dalej."

    def test_nie_rusza_liknu_markdown(self) -> None:
        text = "Zobacz [1](https://example.org) po szczegóły."
        assert normalize_model_output(text) == text

    def test_nie_rusza_roku_w_nawiasie(self) -> None:
        text = "Ustawa z 2001 r. [2024] nie jest odnośnikiem."
        assert normalize_model_output(text) == text

    def test_nie_rusza_nawiasu_bez_cyfry(self) -> None:
        text = "Przypis [abc] i [ ] zostają."
        assert normalize_model_output(text) == text

    def test_tresc_z_odnosnikami_jest_uzywalna(self) -> None:
        """Sedno P1: przed poprawką `is_usable` zwracało `False` dla tej treści."""
        body = normalize_model_output(MODEL_OUTPUT_PLAIN)
        assert is_usable(body) is True

    def test_bez_normalizacji_tresc_była_odrzucana(self) -> None:
        """Kontrola: surowa odpowiedź modelu nie przechodzi progu używalności."""
        assert is_usable(MODEL_OUTPUT_PLAIN) is False


class TestFootnoteDefinitions:
    """P3 — blok definicji przypisów nie jest treścią pisma."""

    def test_usuwa_blok_definicji(self) -> None:
        body = normalize_model_output(MODEL_OUTPUT)
        assert "[^1]:" not in body
        assert "[^2]:" not in body
        assert "[^3]:" not in body
        # Definicja znika, ale to samo zdanie w treści merytorycznej zostaje.
        assert "Zgodnie z art. 13 ust. 1 ustawy o dostępie" in body

    def test_zostawia_tresc_merytoryczna(self) -> None:
        body = normalize_model_output(MODEL_OUTPUT)
        assert "## Podstawa prawna" in body
        assert "## Odpowiedź" in body
        assert "Wynagrodzenia pracowników samorządowych" in body

    def test_usuwa_definicje_zapisane_bez_daszkowania(self) -> None:
        """Model myli oba formaty — `[1]: …` też jest definicją, nie zdaniem."""
        body = normalize_model_output("Treść [1].\n\n[1]: art. 13 ustawy")
        assert body == "Treść [^1]."

    def test_usuwa_definicje_w_srodku_tresci(self) -> None:
        text = "Akapit [1].\n\n[^1]: art. 13\n\nDalszy akapit [2]."
        body = normalize_model_output(text)
        assert "[^1]:" not in body
        assert "Dalszy akapit [^2]." in body

    def test_nie_rusza_zdania_zawierajacego_dwukropek(self) -> None:
        text = "Podstawa: art. 13 ustawy [1]."
        assert normalize_model_output(text) == "Podstawa: art. 13 ustawy [^1]."


class TestCombined:
    """Oba defekty naraz, na próbce z raportu."""

    def test_pelna_normalizacja(self) -> None:
        body = normalize_model_output(MODEL_OUTPUT)
        assert "[^1]" in body
        assert "[^2]" in body
        assert "[^3]" in body
        assert "[^1]:" not in body
        assert body.rstrip().endswith("[^3].")

    def test_zdania_po_normalizacji_maja_pokrycie(self) -> None:
        body = normalize_model_output(MODEL_OUTPUT)
        unsupported = find_unsupported(body, {1, 2, 3})
        assert unsupported == []

    def test_odniesienie_do_nieistniejacego_zrodla_zostaje_wykryte(self) -> None:
        body = normalize_model_output(MODEL_OUTPUT)
        unsupported = find_unsupported(body, {1})
        assert any("Wynagrodzenia pracowników" in sentence for sentence in unsupported)
