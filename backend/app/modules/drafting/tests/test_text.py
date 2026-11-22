"""Podział na zdania i format daty — wspólne dla szablonu i kontroli twierdzeń.

P11 z raportu z testów na żywym Mistralu: `_SENTENCE_END` dzieliło zdanie po
każdej kropce przed wielką literą, więc „(Dz. U. z 2023 r. poz. 1479)" pękało
w środku cytatu aktu. Pierwszy fragment zostawał bez odnośnika i trafiał do
`unsupported` jako twierdzenie bez źródła — w pomiarach 6 z 10 projektów.
"""

from __future__ import annotations

from datetime import date

from app.modules.drafting.text import (
    ABBREVIATIONS,
    ends_with_abbreviation,
    format_date_pl,
    split_sentences,
)


class TestSplitSentences:
    """P11 — skróty urzędowe nie kończą zdania."""

    def test_dz_u_nie_dzieli_zdania(self) -> None:
        text = (
            "Odpowiedź przygotowano na podstawie ustawy (Dz. U. z 2023 r. poz. 1479) "
            "[^1]."
        )
        assert split_sentences(text) == [text]

    def test_dz_u_w_srodku_dluzszego_zdania(self) -> None:
        text = (
            "Podstawę stanowi art. 13 ustawy z dnia 6 września 2001 r. o dostępie "
            "do informacji publicznej (Dz. U. z 2023 r. poz. 1479) [^1]. "
            "Termin wynosi 14 dni [^2]."
        )
        sentences = split_sentences(text)
        assert len(sentences) == 2
        assert sentences[0].endswith("[^1].")
        assert sentences[1].startswith("Termin wynosi")

    def test_zwykla_kropka_dzieli_zdania(self) -> None:
        assert split_sentences("Pierwsze zdanie. Drugie zdanie.") == [
            "Pierwsze zdanie.",
            "Drugie zdanie.",
        ]

    def test_skrot_przed_nazwiskiem(self) -> None:
        text = "Pismo podpisał dr Jan Kowalski. Sprawa jest zamknięta."
        assert split_sentences(text) == [
            "Pismo podpisał dr Jan Kowalski.",
            "Sprawa jest zamknięta.",
        ]

    def test_skrot_na_koncu_zdania_nie_skleja_dwoch(self) -> None:
        """Kropka po pełnym słowie zamyka zdanie, nawet gdy stoi przed nim skrót."""
        text = "Termin upłynął 2 marca 2026 r. Sprawa pozostaje otwarta."
        assert split_sentences(text) == [
            "Termin upłynął 2 marca 2026 r.",
            "Sprawa pozostaje otwarta.",
        ]

    def test_pusty_tekst(self) -> None:
        assert split_sentences("") == []
        assert split_sentences("   ") == []


class TestEndsWithAbbreviation:
    def test_rozpoznaje_skrot(self) -> None:
        assert ends_with_abbreviation("(Dz.") is True
        assert ends_with_abbreviation("zgodnie z art.") is True
        assert ends_with_abbreviation("w zw.") is True

    def test_nie_rozpoznaje_zwyklego_slowa(self) -> None:
        assert ends_with_abbreviation("Pierwsze zdanie.") is False
        assert ends_with_abbreviation("bez kropki") is False

    def test_nie_rozpoznaje_skrotu_mogacego_konczyc_zdanie(self) -> None:
        assert ends_with_abbreviation("ustawy z 2023 r.") is False

    def test_lista_skrotow_jest_niepusta(self) -> None:
        assert "dz" in ABBREVIATIONS
        assert "art" in ABBREVIATIONS
        assert "ust" in ABBREVIATIONS
        assert "poz" in ABBREVIATIONS
        assert "nr" in ABBREVIATIONS
        assert "t.j" in ABBREVIATIONS

    def test_skroty_mogace_konczyc_zdanie_poza_lista(self) -> None:
        """„r." kończy zdanie („…w 2023 r."), więc nie może sklejać zdań."""
        assert "r" not in ABBREVIATIONS
        assert "np" not in ABBREVIATIONS
        assert "itd" not in ABBREVIATIONS


class TestFormatDatePl:
    def test_data_w_formie_urzedowej(self) -> None:
        assert format_date_pl(date(2026, 3, 2)) == "2 marca 2026"

    def test_pierwszy_i_ostatni_miesiac(self) -> None:
        assert format_date_pl(date(2026, 1, 1)) == "1 stycznia 2026"
        assert format_date_pl(date(2026, 12, 31)) == "31 grudnia 2026"
