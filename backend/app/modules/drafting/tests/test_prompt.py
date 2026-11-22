"""Normalizacja odpowiedzi modelu — format odnośników i definicje przypisów.

Dwa defekty z raportu z testów na żywym Mistralu:

* P1 — model pisze `[1]`, a nie `[^1]`, więc `is_usable` odrzucał poprawną
  treść i 20% projektów po cichu schodziło do szablonu,
* P3 — model dokleja na końcu blok definicji przypisów, który trafiał do
  eksportu DOCX i PDF jako zwykły akapit pisma.
"""

from __future__ import annotations

from app.modules.drafting.prompt import (
    collapse_ref_runs,
    extract_refs,
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


#: Zdanie z podstawy prawnej, które po naprawie P2 zaczęło pękać na „(Dz." (P11).
LEGAL_BASIS = (
    "Niniejsza odpowiedź została przygotowana na podstawie przepisów ustawy "
    "z dnia 6 września 2001 r. o dostępie do informacji publicznej "
    "(Dz. U. z 2023 r. poz. 1479) [^1]."
)


class TestAbbreviations:
    """P11 — skrót „Dz. U." nie może tworzyć fałszywego twierdzenia bez źródła."""

    def test_zdanie_z_dz_u_jest_pokryte(self) -> None:
        assert find_unsupported(LEGAL_BASIS, {1}) == []

    def test_zdanie_nie_jest_rozbijane(self) -> None:
        """Bez naprawy pierwszy fragment kończył się na „(Dz." i nie miał odnośnika."""
        unsupported = find_unsupported(LEGAL_BASIS, {1})
        assert not any(sentence.endswith("(Dz.") for sentence in unsupported)

    def test_zdanie_bez_odnosnika_nadal_jest_wykrywane(self) -> None:
        """Naprawa nie może wyciszyć prawdziwego ostrzeżenia."""
        text = (
            "Ustawa weszła w życie w 2023 r. Wynagrodzenia pracowników "
            "samorządowych są jawne."
        )
        unsupported = find_unsupported(text, {1})
        assert any("Wynagrodzenia pracowników" in sentence for sentence in unsupported)


class TestCollapseRefRuns:
    """P14 — ciąg odnośników pod rząd zwężamy do zakresu."""

    def test_zwęża_przebieg_trzech(self) -> None:
        assert collapse_ref_runs("A [^2][^3][^4] B") == "A [^2]–[^4] B"

    def test_zwęża_dlugi_przebieg(self) -> None:
        run = "".join(f"[^{ref}]" for ref in range(2, 14))
        assert collapse_ref_runs(f"Podstawa {run}.") == "Podstawa [^2]–[^13]."

    def test_dwa_odnosniki_zostaja_bez_zmian(self) -> None:
        assert collapse_ref_runs("A [^2][^3] B") == "A [^2][^3] B"

    def test_przebieg_nieciagly_zostaje_bez_zmian(self) -> None:
        """Zakres kłamałby o treści — 2, 5 i 9 to nie 2–9."""
        assert collapse_ref_runs("A [^2][^5][^9] B") == "A [^2][^5][^9] B"

    def test_zwęża_ciagly_fragment_nieciaglego_przebiegu(self) -> None:
        """Model dopisał na końcu odległy numer — reszta ciągu wciąż się zwęża."""
        run = "".join(f"[^{ref}]" for ref in [*range(2, 13), 16])
        assert collapse_ref_runs(f"Podstawa {run}.") == "Podstawa [^2]–[^12][^16]."

    def test_dwa_krotkie_fragmenty_zostaja(self) -> None:
        assert collapse_ref_runs("A [^2][^3][^5][^6] B") == "A [^2][^3][^5][^6] B"

    def test_zakres_rozwija_sie_w_cytowaniach(self) -> None:
        collapsed = collapse_ref_runs("A [^2][^3][^4][^5] B")
        assert extract_refs(collapsed) == [2, 3, 4, 5]

    def test_kolejnosc_pierwszego_wystapienia(self) -> None:
        body = "A [^7] B [^2][^3][^4] C [^1]"
        assert extract_refs(collapse_ref_runs(body)) == [7, 2, 3, 4, 1]

    def test_zdanie_z_zakresem_jest_pokryte(self) -> None:
        body = collapse_ref_runs("Podstawa prawna [^2][^3][^4].")
        assert find_unsupported(body, {2, 3, 4}) == []


class TestIsoDates:
    """P15 — pismo urzędowe nie zawiera daty w formacie ISO."""

    def test_data_iso_na_zapis_urzedowy(self) -> None:
        assert normalize_model_output("Termin upływa 2026-03-02.") == (
            "Termin upływa 2 marca 2026 r."
        )

    def test_dwie_daty_w_zdaniu(self) -> None:
        body = normalize_model_output("Wpływ 2026-02-20, termin 2026-03-06.")
        assert body == "Wpływ 20 lutego 2026 r., termin 6 marca 2026 r."

    def test_nie_dubluje_skrotu_r(self) -> None:
        assert normalize_model_output("Data 2026-03-16 r.") == "Data 16 marca 2026 r."

    def test_nieczytelna_data_zostaje(self) -> None:
        assert normalize_model_output("Data 2026-13-45.") == "Data 2026-13-45."

    def test_data_bez_zer_wiodacych(self) -> None:
        assert normalize_model_output("2026-01-05") == "5 stycznia 2026 r."
