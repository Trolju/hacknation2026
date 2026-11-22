"""Pomocnicze funkcje tekstowe wspólne dla szablonu i kontroli twierdzeń.

Dwie rzeczy trzymają pismo w formie urzędowej:

1. `split_sentences` dzieli akapit na zdania, ale nie po skrótach. „Dz. U."
   to standardowy zapis w pismach urzędowych — kropka po „Dz" nie kończy
   zdania, a podział w tym miejscu zostawiał fragment cytatu aktu bez
   odnośnika i tworzył fałszywe ostrzeżenie o twierdzeniu bez źródła.
2. `format_date_pl` podaje datę po polsku („20 lutego 2026"), bo pismo
   urzędowe nie zawiera daty w formacie ISO.
"""

from __future__ import annotations

import re
from datetime import date

MONTHS: tuple[str, ...] = (
    "stycznia",
    "lutego",
    "marca",
    "kwietnia",
    "maja",
    "czerwca",
    "lipca",
    "sierpnia",
    "września",
    "października",
    "listopada",
    "grudnia",
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])")

#: Skróty, po których kropka nigdy nie zamyka zdania w piśmie urzędowym.
#: Lista obejmuje zapis aktów prawnych („Dz. U.", „t.j.", „art.", „ust.",
#: „poz.") oraz skróty tytułów i adresów, które stoją przed nazwą.
#:
#: Świadomie poza listą: „r.", „np.", „itd.", „tzn.", „tzw.", „tys.", „mln.".
#: Te mogą stać na końcu zdania („…w 2023 r. Sprawa pozostaje otwarta."),
#: a sklejenie dwóch zdań ukryłoby prawdziwe twierdzenie bez źródła — czyli
#: zamieniłoby fałszywy alarm na przeoczenie.
ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "al",
        "art",
        "dn",
        "dr",
        "dz",
        "gen",
        "godz",
        "hab",
        "inż",
        "ks",
        "lit",
        "m.in",
        "mgr",
        "nr",
        "os",
        "pkt",
        "płk",
        "poz",
        "prof",
        "rozdz",
        "sp",
        "str",
        "sygn",
        "św",
        "t.j",
        "u",
        "ul",
        "ust",
        "w.g",
        "wg",
        "ww",
        "zał",
        "zm",
        "zw",
    }
)

#: Ostatnie słowo fragmentu razem z kropką — kandydat na skrót.
_TRAILING_TOKEN = re.compile(
    r"([0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż][0-9A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż./]*\.)$"
)


def format_date_pl(value: date) -> str:
    """Data w formie urzędowej: „20 lutego 2026”."""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def ends_with_abbreviation(text: str) -> bool:
    """Czy fragment kończy się skrótem, po którym kropka nie zamyka zdania."""
    match = _TRAILING_TOKEN.search(text)
    if match is None:
        return False
    return match.group(1).rstrip(".").lower() in ABBREVIATIONS


def split_sentences(line: str) -> list[str]:
    """Dzieli akapit na zdania, nie rozbijając skrótów urzędowych.

    Fragment, po którym stoi skrót, jest sklejany z następnym — dopiero
    kropka po pełnym słowie zamyka zdanie.
    """
    parts = [part.strip() for part in _SENTENCE_END.split(line) if part.strip()]
    merged: list[str] = []
    for part in parts:
        if merged and ends_with_abbreviation(merged[-1]):
            merged[-1] = f"{merged[-1]} {part}"
        else:
            merged.append(part)
    return merged
