"""Adapter realny anonimizacji (WS6) — `NerAnonymizer`.

Detektory regułowe rozszerzone względem atrapy o:

- rozpoznawanie nazwisk bez gazetteeru: wzorce kontekstowe („Pan/Pani",
  „wnioskodawca", formy grzecznościowe) oraz końcówki nazwiskowe
  (-ski/-cki/-czyk/-wicz),
- adresy bez prefiksu ulicy i kody pocztowe w formacie `XX-XXX`,
- numery ksiąg wieczystych i sygnatury akt sądowych (kategoria `inne`),
- opcjonalny przebieg NER przez spaCy — import w `try/except`, brak modelu
  oznacza cichą degradację do reguł.

Zakaz fałszywych trafień: numery wniosków `UDIP.*` i sygnatury `ZP.*` są
wycinane z tekstu przed dopasowaniem wzorców numerycznych, więc nigdy nie
trafiają do kategorii `nip`, `regon` ani `pesel`.

Konwencja zakresów `imie_nazwisko`: span obejmuje imię i nazwisko oraz
poprzedzający je tytuł zawodowy lub służbowy („inż.", „mgr", „starszy
inspektor", „Dyrektor Wydziału Oświaty"). Zaimki i rzeczowniki opisujące rolę
(„Pan", „Pani", „wnioskodawca") nie wchodzą do spanu — są tylko sygnałem
kontekstowym.
"""

from __future__ import annotations

import re
from typing import Any, Final, Protocol

from app.contracts import (
    AnonymizerMetrics,
    ApplyRequest,
    ApplyResult,
    DetectRequest,
    Span,
    SpanCategory,
)
from app.modules.anonymize.metrics import evaluate_samples, load_heldout

# ─────────────────────────── opcjonalny NER ────────────────────────────
try:  # pragma: no cover - zależne od środowiska
    import spacy
except Exception:  # noqa: BLE001 - brak spaCy nie może wywalić aplikacji
    spacy = None  # type: ignore[assignment]

_NER_MODEL: Final[str] = "pl_core_news_sm"

# ────────────────────────────── znaki ──────────────────────────────────
_UPPER: Final[str] = "A-ZĄĆĘŁŃÓŚŹŻ"
_LOWER: Final[str] = "a-ząćęłńóśźż"
_UPPER_CHARS: Final[frozenset[str]] = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZĄĆĘŁŃÓŚŹŻ")
_WORD: Final[str] = rf"[{_UPPER}][{_LOWER}]+(?:-[{_UPPER}][{_LOWER}]+)*"
_TOKEN: Final[re.Pattern[str]] = re.compile(
    rf"[{_UPPER}{_LOWER}][{_UPPER}{_LOWER}0-9]*"
    rf"(?:-[{_UPPER}{_LOWER}][{_UPPER}{_LOWER}0-9]*)*"
)

# ──────────────────────── fragmenty chronione ──────────────────────────
# Numery wniosków i sygnatury postępowań: nie są danymi osobowymi i nie wolno
# klasyfikować ich jako NIP/REGON/PESEL.
_PROTECTED: Final[re.Pattern[str]] = re.compile(
    r"\bUDIP\.[0-9A-Za-z.]+"
    r"|\bZP\.[0-9A-Za-z.]+"
    r"|\bZnak\s+sprawy:?\s*[0-9A-Za-z./-]+"
)

# ──────────────────────────── gazetteer imion ──────────────────────────
# Formy odmienione wyprowadzamy z rdzenia (obcięcie 1-2 znaków), więc lista
# zawiera tylko formy podstawowe. Imiona nieregularne mają jawne formy.
_FIRST_NAME_BASES: Final[tuple[str, ...]] = (
    "Adam",
    "Adrian",
    "Agnieszka",
    "Agata",
    "Aleks",
    "Aleksander",
    "Aleksandra",
    "Alicja",
    "Andrzej",
    "Aneta",
    "Anna",
    "Antoni",
    "Arkadiusz",
    "Artur",
    "Barbara",
    "Bartosz",
    "Beata",
    "Błażej",
    "Bogdan",
    "Bogumiła",
    "Bożena",
    "Bruno",
    "Cezary",
    "Czesław",
    "Czesława",
    "Damian",
    "Danuta",
    "Dariusz",
    "Dawid",
    "Dominik",
    "Dorota",
    "Edyta",
    "Elżbieta",
    "Emil",
    "Emilia",
    "Ewelina",
    "Filip",
    "Franciszek",
    "Gabriela",
    "Grażyna",
    "Grzegorz",
    "Halina",
    "Hanna",
    "Henryk",
    "Igor",
    "Ilona",
    "Irena",
    "Ireneusz",
    "Iwona",
    "Izabela",
    "Jacek",
    "Jadwiga",
    "Jakub",
    "Jan",
    "Janina",
    "Janusz",
    "Jarosław",
    "Jerzy",
    "Joanna",
    "Jolanta",
    "Józef",
    "Julia",
    "Justyna",
    "Kacper",
    "Kamil",
    "Kamila",
    "Karol",
    "Karolina",
    "Katarzyna",
    "Kazimierz",
    "Kinga",
    "Klaudia",
    "Konrad",
    "Krystian",
    "Krystyna",
    "Krzysztof",
    "Laura",
    "Lena",
    "Leon",
    "Leszek",
    "Liliana",
    "Lucyna",
    "Łucja",
    "Łukasz",
    "Maciej",
    "Magdalena",
    "Maja",
    "Maksymilian",
    "Malwina",
    "Marcin",
    "Marek",
    "Maria",
    "Marian",
    "Mariusz",
    "Marta",
    "Marzena",
    "Mateusz",
    "Michał",
    "Mikołaj",
    "Milena",
    "Mirosław",
    "Miłosz",
    "Monika",
    "Natalia",
    "Nina",
    "Norbert",
    "Olaf",
    "Olga",
    "Oliwia",
    "Oliwier",
    "Oskar",
    "Patrycja",
    "Patryk",
    "Paulina",
    "Paweł",
    "Piotr",
    "Przemysław",
    "Radosław",
    "Rafał",
    "Renata",
    "Robert",
    "Roman",
    "Ryszard",
    "Sabina",
    "Sandra",
    "Sebastian",
    "Sławomir",
    "Stanisław",
    "Stefania",
    "Sylwester",
    "Sylwia",
    "Szymon",
    "Tadeusz",
    "Teresa",
    "Tomasz",
    "Tymon",
    "Urszula",
    "Waldemar",
    "Wanda",
    "Weronika",
    "Wiesław",
    "Wiesława",
    "Wiktoria",
    "Wiktor",
    "Wioletta",
    "Witold",
    "Władysław",
    "Wojciech",
    "Zbigniew",
    "Zdzisław",
    "Zofia",
    "Zuzanna",
    "Zygmunt",
    "Żaneta",
)

# Imiona, których rdzeń jest zbyt krótki lub zbyt wieloznaczny — tylko jawne formy.
_SHORT_NAME_FORMS: Final[dict[str, tuple[str, ...]]] = {
    "Ewa": ("Ewa", "Ewy", "Ewie", "Ewę", "Ewą"),
    "Jan": ("Jan", "Jana", "Janowi", "Janem", "Janie"),
    "Maja": ("Maja", "Mai", "Maję", "Mają"),
}

# Imiona z obocznością tematu (Marek → Marka, Paweł → Pawła).
_IRREGULAR_NAME_FORMS: Final[dict[str, tuple[str, ...]]] = {
    "Franciszek": ("Franciszka", "Franciszkowi", "Franciszkiem"),
    "Jacek": ("Jacka", "Jackowi", "Jackiem"),
    "Kacper": ("Kacpra", "Kacprowi", "Kacprem"),
    "Leszek": ("Leszka", "Leszkowi", "Leszkiem"),
    "Marek": ("Marka", "Markowi", "Markiem"),
    "Paweł": ("Pawła", "Pawłowi", "Pawłem"),
    "Sylwester": ("Sylwestra", "Sylwestrowi", "Sylwestrem"),
}


def _build_name_index() -> tuple[frozenset[str], frozenset[str]]:
    exact: set[str] = set()
    stems: set[str] = set()
    for base in _FIRST_NAME_BASES:
        low = base.lower()
        exact.add(low)
        exact.update(form.lower() for form in _IRREGULAR_NAME_FORMS.get(base, ()))
        if base in _SHORT_NAME_FORMS:
            exact.update(form.lower() for form in _SHORT_NAME_FORMS[base])
            continue
        for cut in (0, 1, 2):
            stem = low[: len(low) - cut] if cut else low
            if len(stem) >= 3:
                stems.add(stem)
    return frozenset(exact), frozenset(stems)


_NAME_EXACT, _NAME_STEMS = _build_name_index()

# ──────────────────────── słowa niebędące nazwiskami ──────────────────
# Rzeczowniki instytucji, funkcje, przymiotniki odmiejscowe i nazwy miast.
# Bez tej listy reguła końcówek -ski/-cki łapałaby „Zarząd Dróg Miejskich".
_NOT_A_NAME: Final[frozenset[str]] = frozenset(
    word.lower()
    for word in (
        # instytucje i jednostki
        "Urząd", "Urzędu", "Urzędzie", "Miasto", "Miasta", "Mieście", "Gmina",
        "Gminy", "Gminie", "Powiat", "Powiatu", "Województwo", "Województwa",
        "Wydział", "Wydziału", "Wydziale", "Wydziały", "Wydziałów", "Biuro",
        "Biura", "Biurze", "Biur", "Referat", "Referatu", "Referacie",
        "Referaty", "Referatów", "Stanowisko", "Stanowiska", "Dział", "Działu",
        "Sekcja", "Sekcji", "Pion", "Pionu", "Oddział", "Oddziału", "Filia",
        "Filii", "Placówka", "Placówki", "Jednostka", "Jednostki", "Komórka",
        "Komórki", "Rada", "Rady", "Radzie", "Zarząd", "Zarządu", "Zarządzie",
        "Komisja", "Komisji", "Komitet", "Komitetu", "Kolegium", "Kolegium",
        "Sąd", "Sądu", "Sądzie", "Trybunał", "Trybunału", "Prokuratura",
        "Prokuratury", "Policja", "Policji", "Straż", "Straży", "Komenda",
        "Komendy", "Szkoła", "Szkoły", "Szkole", "Szkół", "Przedszkole",
        "Przedszkola", "Liceum", "Technikum", "Uniwersytet", "Uniwersytetu",
        "Politechnika", "Politechniki", "Akademia", "Akademii", "Instytut",
        "Instytutu", "Centrum", "Centrum", "Zakład", "Zakładu", "Zakłady",
        "Zakładów", "Przedsiębiorstwo", "Przedsiębiorstwa", "Spółka", "Spółki",
        "Fundacja", "Fundacji", "Stowarzyszenie", "Stowarzyszenia", "Związek",
        "Związku", "Izba", "Izby", "Agencja", "Agencji", "Ministerstwo",
        "Ministerstwa", "Kancelaria", "Kancelarii", "Bank", "Banku", "Szpital",
        "Szpitala", "Przychodnia", "Przychodni", "Biblioteka", "Biblioteki",
        "Muzeum", "Teatr", "Teatru", "Filharmonia", "Filharmonii", "Opera",
        "Opery", "Galeria", "Galerii", "Archiwum", "Archiwum", "Park", "Parku",
        "Ogród", "Ogrodu", "Plac", "Placu", "Ulica", "Ulicy", "Aleja", "Aleje",
        "Alej", "Osiedle", "Osiedla", "Rondo", "Ronda", "Skwer", "Skweru",
        "Dzielnica", "Dzielnicy", "Region", "Regionu", "Okręg", "Okręgu",
        "Rejon", "Rejonu", "Klub", "Klubu", "Zespół", "Zespołu", "Drużyna",
        "Drużyny", "Towarzystwo", "Towarzystwa", "Federacja", "Federacji",
        "Konfederacja", "Kongres", "Partia", "Partii", "Koalicja", "Koalicji",
        "Inicjatywa", "Inicjatywy", "Ruch", "Ruchu", "Forum", "Forum",
        "Konferencja", "Konferencji", "Sympozjum", "Kongres", "Fundusz",
        "Funduszu", "Fundusze", "Funduszy", "Program", "Programu", "Projekt",
        "Projektu", "Projekty", "Projektów", "Zadanie", "Zadania", "Zadań",
        "Cel", "Celu", "Cele", "Celów", "Potrzeba", "Potrzeby", "Potrzeb",
        "Działanie", "Działania", "Działań", "Inwestycja", "Inwestycji",
        "Remont", "Remontu", "Remonty", "Remontów", "Robota", "Roboty",
        "Robót", "Usługa", "Usługi", "Usług", "Dostawa", "Dostawy", "Dostaw",
        "Zamówienie", "Zamówienia", "Zamówień", "Przetarg", "Przetargu",
        "Postępowanie", "Postępowania", "Postępowań", "Umowa", "Umowy", "Umów",
        "Faktura", "Faktury", "Faktur", "Pismo", "Pisma", "Pism", "Sprawa",
        "Sprawy", "Spraw", "Wniosek", "Wniosku", "Wnioski", "Wniosków",
        "Podanie", "Podania", "Skarga", "Skargi", "Skarg", "Odwołanie",
        "Odwołania", "Zażalenie", "Zażalenia", "Decyzja", "Decyzji",
        "Postanowienie", "Postanowienia", "Uchwała", "Uchwały", "Uchwał",
        "Zarządzenie", "Zarządzenia", "Zarządzeń", "Protokół", "Protokołu",
        "Protokoły", "Protokołów", "Opinia", "Opinii", "Ekspertyza",
        "Ekspertyzy", "Analiza", "Analizy", "Raport", "Raportu", "Raporty",
        "Dokument", "Dokumentu", "Dokumenty", "Dokumentów", "Załącznik",
        "Załącznika", "Załączniki", "Materiał", "Materiału", "Materiały",
        "Materiałów", "Dane", "Danych", "Informacja", "Informacji",
        "Osoba", "Osoby", "Osób", "Mieszkaniec", "Mieszkańca", "Mieszkańcy",
        "Mieszkańców", "Pracownik", "Pracownika", "Pracownicy", "Pracowników",
        "Interesant", "Interesanta", "Interesanci", "Klient", "Klienta",
        "Klienci", "Klientów", "Petent", "Petenta", "Petenci", "Petentów",
        "Uczestnik", "Uczestnika", "Uczestnicy", "Uczestników", "Członek",
        "Członka", "Członkowie", "Członków", "Radny", "Radnego", "Radni",
        "Radnych", "Sołtys", "Sołtysa", "Wójt", "Wójta", "Burmistrz",
        "Burmistrza", "Prezydent", "Prezydenta", "Starosta", "Starosty",
        "Wojewoda", "Wojewody", "Marszałek", "Marszałka", "Minister",
        "Ministra", "Dyrektor", "Dyrektora", "Kierownik", "Kierownika",
        "Naczelnik", "Naczelnika", "Inspektor", "Inspektora", "Inspektorzy",
        "Inspektorów", "Referent", "Referenta", "Referenci", "Referentów",
        "Specjalista", "Specjalisty", "Specjaliści", "Specjalistów", "Ekspert",
        "Eksperta", "Eksperci", "Ekspertów", "Doradca", "Doradcy", "Doradców",
        "Asystent", "Asystenta", "Asystenci", "Asystentów", "Sekretarka",
        "Sekretarki", "Sekretariat", "Sekretariatu", "Referendarz",
        "Referendarza", "Aplikant", "Aplikanta", "Stażysta", "Stażysty",
        "Wolontariusz", "Wolontariusza", "Kurator", "Kuratora", "Komornik",
        "Komornika", "Syndyk", "Syndyka", "Likwidator", "Likwidatora",
        "Zarządca", "Zarządcy", "Administrator", "Administratora", "Kontroler",
        "Kontrolera", "Audytor", "Audytora", "Rewident", "Rewidenta", "Biegły",
        "Biegłego", "Rzeczoznawca", "Rzeczoznawcy", "Architekt", "Architekta",
        "Geodeta", "Geodety", "Urbanista", "Urbanisty", "Konserwator",
        "Konserwatora", "Sędzia", "Sędziego", "Prokurator", "Prokuratora",
        "Notariusz", "Notariusza", "Adwokat", "Adwokata", "Radca", "Radcy",
        "Lekarz", "Lekarza", "Pielęgniarka", "Pielęgniarki", "Nauczyciel",
        "Nauczyciela", "Profesor", "Profesora", "Doktor", "Doktora",
        "Magister", "Magistra", "Inżynier", "Inżyniera", "Prezes",
        "Prezesa", "Wiceprezes", "Wiceprezesa", "Zastępca", "Zastępcy",
        "Pełnomocnik", "Pełnomocnika", "Przedstawiciel", "Przedstawiciela",
        "Świadek", "Świadka", "Obywatel", "Obywatela", "Pan", "Pana",
        "Pani", "Panią", "Państwo", "Państwa", "Państwu", "Wnioskodawca",
        "Wnioskodawcy", "Wnioskodawczyni", "Skarżący", "Skarżącego",
        "Zainteresowany", "Zainteresowanego", "Podpisany", "Podpisanego",
        # przymiotniki odmiejscowe i urzędowe
        "Wojewódzki", "Wojewódzkiego", "Miejski", "Miejskiego", "Miejska",
        "Miejskiej", "Miejskich", "Gminny", "Gminnego", "Powiatowy",
        "Powiatowego", "Rejonowy", "Rejonowego", "Okręgowy", "Okręgowego",
        "Apelacyjny", "Apelacyjnego", "Najwyższy", "Najwyższego", "Naczelny",
        "Naczelnego", "Administracyjny", "Administracyjnego", "Cywilny",
        "Cywilnego", "Karny", "Karnego", "Gospodarczy", "Gospodarczego",
        "Handlowy", "Handlowego", "Skarbowy", "Skarbowego", "Publiczny",
        "Publicznego", "Publiczna", "Publicznej", "Polski", "Polskiego",
        "Polska", "Polskiej", "Narodowy", "Narodowego", "Narodowa",
        "Narodowej", "Państwowy", "Państwowego", "Państwowa", "Państwowej",
        "Europejski", "Europejskiego", "Europejska", "Europejskiej", "Unia",
        "Unii", "Rzeczpospolita", "Rzeczypospolitej", "Krajowy", "Krajowego",
        "Krajowa", "Krajowej", "Regionalny", "Regionalnego", "Regionalna",
        "Regionalnej", "Lokalny", "Lokalnego", "Samorządowy", "Samorządowego",
        "Samorządowa", "Samorządowej", "Gospodarka", "Gospodarki",
        "Gospodarce", "Ochrona", "Ochrony", "Środowisko", "Środowiska",
        "Zdrowie", "Zdrowia", "Edukacja", "Edukacji", "Kultura", "Kultury",
        "Sport", "Sportu", "Turystyka", "Turystyki", "Transport",
        "Transportu", "Komunikacja", "Komunikacji", "Infrastruktura",
        "Infrastruktury", "Architektura", "Architektury", "Geodezja",
        "Geodezji", "Planowanie", "Planowania", "Rozwój", "Rozwoju",
        "Współpraca", "Współpracy", "Obsługa", "Obsługi", "Administracja",
        "Administracji", "Organizacja", "Organizacji", "Informatyka",
        "Informatyki", "Bezpieczeństwo", "Bezpieczeństwa", "Zarządzanie",
        "Zarządzania", "Kontrola", "Kontroli", "Nadzór", "Nadzoru", "Mienie",
        "Mienia", "Nieruchomość", "Nieruchomości", "Lokal", "Lokalu",
        "Lokale", "Lokali", "Mieszkalny", "Mieszkalnego", "Mieszkalne",
        "Mieszkalnych", "Komunalny", "Komunalnego", "Komunalne",
        "Komunalnych", "Oświata", "Oświaty", "Obywatelski", "Obywatelskie",
        "Obywatelskich", "Ewidencja", "Ewidencji", "Ludność", "Ludności",
        "Wojskowy", "Wojskowe", "Wojskowych", "Droga", "Drogi", "Dróg",
        "Zieleń", "Zieleni", "Wodociągi", "Wodociągów", "Energetyka",
        "Energetyki", "Kadry", "Kadr", "Płace", "Płac", "Księgowość",
        "Księgowości", "Finanse", "Finansów", "Budżet", "Budżetu",
        "Kujawski", "Kujawskiego", "Kujawska", "Kujawskiej", "Kujawsko",
        "Pomorski", "Pomorskiego", "Pomorska", "Pomorskiej", "Wielkopolski",
        "Wielkopolskiego", "Mazowiecki", "Mazowieckiego", "Śląski",
        "Śląskiego", "Małopolski", "Małopolskiego", "Podlaski", "Podlaskiego",
        "Lubelski", "Lubelskiego", "Warmiński", "Warmińskiego", "Mazurski",
        "Mazurskiego", "Zachodniopomorski", "Zachodniopomorskiego",
        "Podkarpacki", "Podkarpackiego", "Świętokrzyski", "Świętokrzyskiego",
        "Lubuski", "Lubuskiego", "Łódzki", "Łódzkiego", "Bydgoski",
        "Bydgoskiego", "Bydgoska", "Bydgoskiej", "Toruński", "Toruńskiego",
        "Warszawski", "Warszawskiego", "Krakowski", "Krakowskiego", "Gdański",
        "Gdańskiego", "Poznański", "Poznańskiego", "Wrocławski",
        "Wrocławskiego", "Szczeciński", "Szczecińskiego", "Gdyński",
        "Gdyńskiego", "Olsztyński", "Olsztyńskiego", "Rzeszowski",
        "Rzeszowskiego", "Kielecki", "Kieleckiego", "Opolski", "Opolskiego",
        "Radomski", "Radomskiego", "Płocki", "Płockiego", "Tarnowski",
        "Tarnowskiego", "Koszaliński", "Koszalińskiego", "Legnicki",
        "Legnickiego", "Słupski", "Słupskiego", "Koniński", "Konińskiego",
        "Gliwicki", "Gliwickiego", "Bytomski", "Bytomskiego", "Rybnicki",
        "Rybnickiego", "Elbląski", "Elbląskiego", "Włocławski",
        "Włocławskiego", "Wałbrzyski", "Wałbrzyskiego", "Zamojski",
        "Zamojskiego", "Chełmski", "Chełmskiego", "Sanocki", "Sanockiego",
        "Przemyski", "Przemyskiego", "Leszczyński", "Leszczyńskiego",
        "Kaliski", "Kaliskiego", "Lubiński", "Lubińskiego", "Głogowski",
        "Głogowskiego", "Siedlecki", "Siedleckiego", "Łomżyński",
        "Łomżyńskiego", "Suwalski", "Suwalskiego", "Ełcki", "Ełckiego",
        "Augustowski", "Augustowskiego", "Inowrocławski",
        "Inowrocławskiego", "Brodnicki", "Brodnickiego", "Chełmiński",
        "Chełmińskiego", "Koronowski", "Koronowskiego", "Szubiński",
        "Szubińskiego", "Kcyński", "Kcyńskiego", "Kruszwicki",
        "Kruszwickiego", "Nakielski", "Nakielskiego", "Świecki",
        "Świeckiego", "Tucholski", "Tucholskiego", "Żniński", "Żnińskiego",
        "Mogileński", "Mogileńskiego", "Lipnowski", "Lipnowskiego",
        "Rypiński", "Rypińskiego", "Wąbrzeski", "Wąbrzeskiego",
        "Radziejowski", "Radziejowskiego", "Aleksandrowski",
        "Aleksandrowskiego", "Ciechociński", "Ciechocińskiego", "Główny",
        "Głównego", "Starszy", "Starszego", "Młodszy", "Młodszego", "Nowy",
        "Nowego", "Stary", "Starego", "Wielki", "Wielkiego", "Mały",
        "Małego", "Górny", "Górnego", "Dolny", "Dolnego", "Pierwszy",
        "Drugi", "Trzeci", "Czwarty", "Piąty", "Szósty", "Siódmy", "Ósmy",
        "Dziewiąty", "Dziesiąty", "Rok", "Roku", "Miesiąc", "Miesiąca",
        "Dzień", "Dnia", "Tydzień", "Tygodnia", "Kwartał", "Kwartału",
        "Półrocze", "Półrocza", "Sygnatura", "Sygnatury", "Akt", "Akta",
        "Aktach", "Księga", "Księgi", "Wieczysta", "Wieczystej", "Działka",
        "Działki", "Obręb", "Obrębu", "Numer", "Numeru", "Data", "Daty",
        # miasta
        "Bydgoszcz", "Bydgoszczy", "Toruń", "Torunia", "Warszawa",
        "Warszawy", "Kraków", "Krakowa", "Gdańsk", "Gdańska", "Poznań",
        "Poznania", "Wrocław", "Wrocławia", "Łódź", "Łodzi", "Lublin",
        "Lublina", "Szczecin", "Szczecina", "Białystok", "Białegostoku",
        "Gdynia", "Gdyni", "Olsztyn", "Olsztyna", "Rzeszów", "Rzeszowa",
        "Kielce", "Kielc", "Opole", "Opola", "Radom", "Radomia", "Płock",
        "Płocka", "Tarnów", "Tarnowa", "Koszalin", "Koszalina", "Legnica",
        "Legnicy", "Grudziądz", "Grudziądza", "Słupsk", "Słupska", "Konin",
        "Konina", "Gliwice", "Gliwic", "Zabrze", "Zabrza", "Bytom",
        "Bytomia", "Rybnik", "Rybna", "Tychy", "Tychów", "Elbląg",
        "Elbląga", "Włocławek", "Włocławka", "Wałbrzych", "Wałbrzycha",
        "Zamość", "Zamościa", "Chełm", "Chełma", "Ostrołęka", "Ostrołęki",
        "Krosno", "Krosna", "Sanok", "Sanoka", "Przemyśl", "Przemyśla",
        "Piła", "Piły", "Leszno", "Leszna", "Kalisz", "Kalisza", "Lubin",
        "Lubina", "Głogów", "Głogowa", "Siedlce", "Siedlec", "Łomża",
        "Łomży", "Suwałki", "Suwałk", "Ełk", "Ełku", "Augustów",
        "Augustowa", "Inowrocław", "Inowrocławia", "Nakło", "Nakła",
        "Świecie", "Świecia", "Tuchola", "Tucholi", "Sępólno", "Sępólna",
        "Żnin", "Żnina", "Mogilno", "Mogilna", "Lipno", "Lipna", "Rypin",
        "Rypina", "Brodnica", "Brodnicy", "Wąbrzeźno", "Wąbrzeźna",
        "Chełmno", "Chełmna", "Radziejów", "Radziejowa", "Aleksandrów",
        "Aleksandrowa", "Ciechocinek", "Ciechocinka", "Koronowo",
        "Koronowa", "Szubin", "Szubina", "Kcynia", "Kcyni", "Łabiszyn",
        "Łabiszyna", "Barcin", "Barcina", "Pakość", "Pakości", "Janikowo",
        "Janikowa", "Strzelno", "Strzelna", "Kruszwica", "Kruszwicy",
    )
)

# Rzeczowniki, po których para „Wielka Litera Wielka Litera" prawie nigdy nie
# jest nazwiskiem — blokują regułę końcówek nazwiskowych.
_INSTITUTION_TRIGGERS: Final[frozenset[str]] = frozenset(
    word.lower()
    for word in (
        "Zarząd", "Zarządu", "Rada", "Rady", "Wydział", "Wydziału", "Biuro",
        "Biura", "Referat", "Referatu", "Urząd", "Urzędu", "Fundacja",
        "Fundacji", "Spółka", "Spółki", "Stowarzyszenie", "Stowarzyszenia",
        "Zakład", "Zakładu", "Instytut", "Instytutu", "Centrum", "Szkoła",
        "Szkoły", "Szpital", "Szpitala", "Bank", "Banku", "Sąd", "Sądu",
        "Prokuratura", "Prokuratury", "Komenda", "Komendy", "Straż",
        "Straży", "Agencja", "Agencji", "Ministerstwo", "Ministerstwa",
        "Izba", "Izby", "Związek", "Związku", "Klub", "Klubu", "Zespół",
        "Zespołu", "Dział", "Działu", "Sekcja", "Sekcji", "Pion", "Pionu",
        "Oddział", "Oddziału", "Filia", "Filii", "Placówka", "Placówki",
        "Jednostka", "Jednostki", "Komisja", "Komisji", "Komitet",
        "Komitetu", "Kolegium", "Trybunał", "Trybunału", "Uniwersytet",
        "Politechnika", "Akademia", "Przedsiębiorstwo", "Przedsiębiorstwa",
        "Kancelaria", "Kancelarii", "Przychodnia", "Przychodni",
        "Biblioteka", "Biblioteki", "Muzeum", "Teatr", "Teatru", "Opera",
        "Opery", "Galeria", "Galerii", "Archiwum", "Park", "Parku", "Ogród",
        "Ogrodu", "Towarzystwo", "Towarzystwa", "Federacja", "Federacji",
        "Fundusz", "Funduszu", "Dzielnica", "Dzielnicy", "Okręg", "Okręgu",
        "Rejon", "Rejonu", "Region", "Regionu", "Usługa", "Usługi", "Usług",
        "Firma", "Firmy", "Firm", "Spółdzielnia", "Spółdzielni", "Grupa",
        "Grupy", "Holding", "Korporacja", "Zakłady", "Zakładów", "Handel",
        "Produkcja", "Budownictwo", "Transport", "Naprawa", "Serwis",
        "Sklep", "Hurtownia", "Restauracja", "Hotel", "Piekarnia",
        "Cukiernia", "Apteka", "Warsztat", "Technika", "Technologie",
        "Systemy", "Instalacje", "Budowa", "Prace", "Doradztwo",
        "Szkolenia", "Marketing", "Reklama", "Studio", "Media",
    )
)

# ──────────────────────── końcówki nazwiskowe ──────────────────────────
_SURNAME_END: Final[re.Pattern[str]] = re.compile(
    r"(?:"
    r"ski|skiego|skiemu|skim|skich|skimi|ska|skiej|ską|"
    r"cki|ckiego|ckiemu|ckim|ckich|ckimi|cka|ckiej|cką|"
    r"dzki|dzkiego|dzkiemu|dzkim|dzkich|dzka|dzkiej|dzką|"
    r"czyk|czyka|czykiem|czykowa|czykowie|czyków|"
    r"wicz|wicza|wiczem|wiczowa|"
    r"icz|icza|iczem"
    r")$"
)

# Przymiotnikowe końcówki firm i instytucji — pierwszy wyraz takiej pary nie
# jest imieniem („Usługi Transportowe Kowalczyk", „Nadwiślańskie Zakłady").
_ADJECTIVAL_END: Final[re.Pattern[str]] = re.compile(
    r"(?:owe|owy|owa|owych|owej|owym|ych|ich|imi|ymi|skie|ckie|dzkie|cze|alne|alny|alna)$"
)

# ──────────────────────── formy grzecznościowe ─────────────────────────
_CONTEXT_EXACT: Final[frozenset[str]] = frozenset(
    {"pan", "pani", "pana", "panią", "państwo", "państwa", "państwu"}
)
_CONTEXT_PREFIXES: Final[tuple[str, ...]] = (
    "wnioskodawc",
    "wnioskodawczyn",
    "skarżąc",
    "petent",
    "zainteresowan",
    "pełnomocnic",
    "przedstawiciel",
    "pracownic",
    "obywatel",
    "mieszkańc",
    "podpisan",
    "podpisał",
    "podpisała",
    "świadek",
    "świadk",
    "interesant",
    "klient",
    "uczestnik",
    "członek",
    "członk",
    "złożył",
    "złożyła",
    "wniósł",
    "wniosła",
    "okazał",
    "okazała",
    "przedłożył",
    "przedłożyła",
    "potwierdził",
    "potwierdziła",
    "odebrał",
    "odebrała",
    "przyjął",
    "przyjęła",
)

# ──────────────────────── tytuły wchodzące w span ──────────────────────
_TITLE_ANCHOR: Final[re.Pattern[str]] = re.compile(
    rf"(?<!\w)(?:"
    rf"(?:Dyrektor(?:a)?|Dyrektorka|Naczelnik(?:a)?|Naczelniczka|Kierownik(?:a)?"
    rf"|Kierowniczka|Zastęp(?:ca|cy)|Prezydent(?:a)?|Sekretarz(?:a)?"
    rf"|Skarbnik(?:a)?|Komendant(?:a)?|Starost(?:a|y)|Wojewod(?:a|y)"
    rf"|Marszał(?:ek|ka)|Burmistrz(?:a)?|Wójt(?:a)?)"
    rf"(?:\s+(?:Dyrektora|Naczelnika|Kierownika))?"
    rf"\s+(?:Wydziału|Biura|Referatu|Miasta|Gminy|Urzędu|Powiatu|Województwa)"
    rf"(?:\s+(?:(?:i|w|we|z|ze|do|na|im\.?)\s+)?{_WORD})*"
    rf"|(?:starszy|młodszy|główny|nad|starsza|młodsza|główna)?\s*"
    rf"(?:inspektor(?:a)?|podinspektor(?:a)?|specjalista|specjalistka"
    rf"|referent(?:a)?|referentka|komisarz(?:a)?|nadkomisarz(?:a)?|aspirant(?:a)?)"
    rf"|(?:inż\.|mgr|dr|dr\s+hab\.|prof\.|lek\.|mec\.)(?:\s+inż\.)?"
    rf")\s*$"
)

# ──────────────────────────── wzorce regułowe ──────────────────────────
_POSTAL: Final[str] = r"\d{2}-\d{3}"
_CITY: Final[str] = rf"{_WORD}(?:\s+{_WORD})?"
_STREET_PREFIX: Final[str] = r"(?:ul|al|pl|os|ulica|aleja|plac|osiedle|rondo|skwer)\.?"
_STREET_NAME: Final[str] = rf"{_WORD}(?:\s+{_WORD}){{0,3}}"
_STREET_NO: Final[str] = r"\d+[a-zA-Z]?(?:/\d+[a-zA-Z]?)?"

_LEGAL_FORM: Final[re.Pattern[str]] = re.compile(
    rf"(?<![\w-])(?!Spółka\b)(?:{_WORD}\s+){{1,4}}"
    r"(?:Sp\.\s*z\s*o\.\s*o\.|sp\.\s*z\s*o\.\s*o\.|S\.A\.|"
    r"spółka\s+z\s+ograniczoną\s+odpowiedzialnością)"
)

PATTERNS: Final[list[tuple[SpanCategory, re.Pattern[str], float]]] = [
    (
        SpanCategory.IBAN,
        re.compile(r"\bPL\d{2}(?:[ ]?\d{4}){6}\b"),
        0.98,
    ),
    (
        SpanCategory.EMAIL,
        re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
        0.97,
    ),
    (
        SpanCategory.PESEL,
        re.compile(r"(?<!\d)\b\d{11}\b(?!\d)"),
        0.95,
    ),
    (
        SpanCategory.NIP,
        re.compile(r"(?<![\d-])\b\d{3}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}\b(?![\d-])"),
        0.9,
    ),
    (
        SpanCategory.REGON,
        re.compile(r"(?<!\d)\b\d{9}\b(?!\d)"),
        0.85,
    ),
    (
        SpanCategory.DOWOD,
        re.compile(r"\b[A-Z]{3}[ ]?\d{6}\b"),
        0.9,
    ),
    (
        SpanCategory.PASZPORT,
        re.compile(r"\b[A-Z]{2}\d{7}\b"),
        0.88,
    ),
    (
        SpanCategory.TELEFON,
        # separator jest wymagany — inaczej 9 cyfr to REGON, a 11 to PESEL
        re.compile(
            r"(?<![\d-])(?:\+48[ -]?)?"
            r"(?:\d{3}[ -]\d{3}[ -]\d{3}|\d{2}[ -]\d{3}[ -]\d{2}[ -]\d{2})"
            r"(?![\d-])"
        ),
        0.9,
    ),
    (
        SpanCategory.ADRES,
        re.compile(
            rf"(?<![\w.]){_STREET_PREFIX}\s*{_STREET_NAME}\s+{_STREET_NO}"
            rf"(?:,\s*{_POSTAL}\s+{_CITY})?"
        ),
        0.9,
    ),
    (
        SpanCategory.ADRES,
        # ulica bez prefiksu, ale z kodem pocztowym na końcu
        re.compile(
            rf"(?<![\w.]){_STREET_NAME}\s+{_STREET_NO},\s*{_POSTAL}\s+{_CITY}"
        ),
        0.85,
    ),
    (
        SpanCategory.ADRES,
        # sam kod pocztowy z miejscowością
        re.compile(rf"(?<![\d-]){_POSTAL}\s+{_CITY}(?![\w])"),
        0.8,
    ),
    (
        SpanCategory.ADRES,
        re.compile(
            rf"skrytk[aę]\s+pocztow[aąy]\s+\d+(?:,\s*{_POSTAL}\s+{_CITY})?"
        ),
        0.85,
    ),
    (
        SpanCategory.DATA_URODZENIA,
        re.compile(r"(?<!\d)\d{1,2}\.\d{2}\.\d{4}(?!\d)"),
        0.8,
    ),
    (
        SpanCategory.INNE,
        # numer księgi wieczystej
        re.compile(r"(?<!\w)KW\s*(?:nr\s*)?[A-Z]{2}\d[A-Z]/\d{8}/\d(?!\d)"),
        0.9,
    ),
    (
        SpanCategory.INNE,
        # sygnatura akt sądowych — z prefiksem „Sygn. akt" albo z częścią miejscową
        re.compile(
            r"(?<!\w)(?:"
            r"Sygn\.\s*akt\s+[IVX]{1,4}\s+[A-Z]{1,3}(?:/[A-Z][a-z]+)?\s+\d{1,5}/\d{2,4}"
            r"|[IVX]{1,4}\s+[A-Z]{1,3}/[A-Z][a-z]+\s+\d{1,5}/\d{2,4}"
            r")(?!\d)"
        ),
        0.9,
    ),
]

# Data w formacie dd.mm.rrrr jest daną osobową tylko po jednym z tych zwrotów.
_DATE_MARKER: Final[re.Pattern[str]] = re.compile(
    r"(?:ur\.|urodzon[ya]|urodzony|Data urodzenia:?)\s*$"
)

_SOURCE_RANK: Final[dict[str, int]] = {"regex": 2, "ner": 1, "llm": 0}


# ─────────────────────────────── scalanie ──────────────────────────────
def _overlaps(a: Span, b: Span) -> bool:
    return a.start < b.end and b.start < a.end


def _rank(span: Span) -> tuple[float, int, int]:
    return (span.confidence, _SOURCE_RANK[span.source], span.end - span.start)


def merge_spans(spans: list[Span]) -> list[Span]:
    """Scalanie wg reguł z `contracts/domain.md` §6.

    Wyższa pewność wygrywa, przy remisie `regex` przed `ner`, a przy dalszym
    remisie dłuższy span. Span zawierający inny span pochłania go.
    """
    ordered = sorted(spans, key=lambda s: (s.start, -(s.end - s.start)))
    out: list[Span] = []
    for span in ordered:
        if not out or not _overlaps(out[-1], span):
            out.append(span)
            continue
        if _rank(span) > _rank(out[-1]):
            out[-1] = span
    return out


# ──────────────────────────── rozpoznawanie ────────────────────────────
def _is_capitalized(token: str) -> bool:
    return bool(token) and token[0] in _UPPER_CHARS


def _is_stop_word(token: str) -> bool:
    return token.lower() in _NOT_A_NAME


def _is_institution(token: str) -> bool:
    return token.lower() in _INSTITUTION_TRIGGERS


def _is_first_name(token: str) -> bool:
    low = token.lower()
    if low in _NAME_EXACT:
        return True
    return any(low.startswith(stem) for stem in _NAME_STEMS)


def _is_context_trigger(token: str) -> bool:
    low = token.lower()
    return low in _CONTEXT_EXACT or low.startswith(_CONTEXT_PREFIXES)


def _adjacent(text: str, end: int, start: int) -> bool:
    """Czy między tokenami jest wyłącznie biały znak (bez kropek i myślników)."""
    return start >= end and text[end:start].strip() == ""


def _looks_like_name_pair(
    tokens: list[tuple[str, int, int]], index: int
) -> bool:
    first, _, _ = tokens[index]
    second, _, _ = tokens[index + 1]
    if _is_stop_word(first) or _is_stop_word(second):
        return False
    if _is_first_name(first):
        return True
    if _ADJECTIVAL_END.search(first):
        return False
    if not _SURNAME_END.search(second) or _SURNAME_END.search(first):
        return False
    return not (index > 0 and _is_institution(tokens[index - 1][0]))


def _extend_with_title(text: str, start: int) -> int:
    match = _TITLE_ANCHOR.search(text[:start])
    return match.start() if match else start


def _name_spans(text: str) -> list[Span]:
    tokens = [(m.group(0), m.start(), m.end()) for m in _TOKEN.finditer(text)]
    ranges: set[tuple[int, int]] = set()

    for index in range(len(tokens) - 1):
        first, first_start, first_end = tokens[index]
        second, second_start, second_end = tokens[index + 1]
        if not (_is_capitalized(first) and _is_capitalized(second)):
            continue
        if not _adjacent(text, first_end, second_start):
            continue
        if _looks_like_name_pair(tokens, index):
            ranges.add((first_start, second_end))

    for index, (token, _, token_end) in enumerate(tokens):
        if not _is_context_trigger(token):
            continue
        if index + 2 >= len(tokens):
            continue
        first, first_start, first_end = tokens[index + 1]
        second, second_start, second_end = tokens[index + 2]
        if not (_is_capitalized(first) and _is_capitalized(second)):
            continue
        if not (
            _adjacent(text, token_end, first_start)
            and _adjacent(text, first_end, second_start)
        ):
            continue
        if _is_stop_word(first) or _is_stop_word(second):
            continue
        ranges.add((first_start, second_end))

    spans: list[Span] = []
    for start, end in sorted(ranges):
        extended = _extend_with_title(text, start)
        spans.append(
            Span(
                start=extended,
                end=end,
                text=text[extended:end],
                category=SpanCategory.IMIE_NAZWISKO,
                confidence=0.85,
                source="regex",
            )
        )
    return spans


def _company_spans(text: str) -> list[Span]:
    return [
        Span(
            start=m.start(),
            end=m.end(),
            text=m.group(0),
            category=SpanCategory.IMIE_NAZWISKO,
            confidence=0.8,
            source="regex",
        )
        for m in _LEGAL_FORM.finditer(text)
    ]


def _overlaps_any(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start < other_end and other_start < end for other_start, other_end in ranges)


class NerLike(Protocol):
    """Cokolwiek, co umie wskazać osoby — spaCy albo podstawiony detektor."""

    def person_spans(self, text: str) -> list[Span]: ...


class _SpacyNer:
    """Cienka nakładka na spaCy — brak modelu oznacza brak przebiegu NER."""

    def __init__(self, model: str = _NER_MODEL) -> None:
        self._model = model
        self._nlp: Any | None = None
        self._loaded = False

    def _load(self) -> Any | None:
        if self._loaded:
            return self._nlp
        self._loaded = True
        if spacy is None:
            return None
        try:  # pragma: no cover - zależne od środowiska
            self._nlp = spacy.load(self._model)
        except Exception:  # noqa: BLE001 - brak modelu to nie błąd aplikacji
            self._nlp = None
        return self._nlp

    @property
    def available(self) -> bool:
        return self._load() is not None

    def person_spans(self, text: str) -> list[Span]:
        nlp = self._load()
        if nlp is None:
            return []
        spans: list[Span] = []
        for entity in nlp(text).ents:  # pragma: no cover - zależne od modelu
            if entity.label_ not in {"persName", "PER"}:
                continue
            spans.append(
                Span(
                    start=entity.start_char,
                    end=entity.end_char,
                    text=entity.text,
                    category=SpanCategory.IMIE_NAZWISKO,
                    confidence=0.7,
                    source="ner",
                )
            )
        return spans


class NerAnonymizer:
    """Anonimizator: reguły + opcjonalny NER, ocena na zbiorze held-out."""

    def __init__(self, ner: NerLike | None = None) -> None:
        self._ner: NerLike = ner if ner is not None else _SpacyNer()

    # ── port ──
    def detect(self, req: DetectRequest) -> list[Span]:
        text = req.text
        allowed = set(req.categories) if req.categories else None
        protected = [(m.start(), m.end()) for m in _PROTECTED.finditer(text)]
        found: list[Span] = []

        for category, pattern, confidence in PATTERNS:
            if allowed is not None and category not in allowed:
                continue
            for match in pattern.finditer(text):
                if _overlaps_any(match.start(), match.end(), protected):
                    continue
                if category is SpanCategory.DATA_URODZENIA and not _DATE_MARKER.search(
                    text[max(0, match.start() - 24) : match.start()]
                ):
                    continue
                found.append(
                    Span(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        category=category,
                        confidence=confidence,
                        source="regex",
                    )
                )

        if allowed is None or SpanCategory.IMIE_NAZWISKO in allowed:
            found.extend(_name_spans(text))
            found.extend(_company_spans(text))
            found.extend(self._ner.person_spans(text))

        return merge_spans(found)

    def apply(self, req: ApplyRequest) -> ApplyResult:
        text = req.text
        valid = [s for s in req.spans if 0 <= s.start < s.end <= len(text)]
        spans = merge_spans(valid)
        result = text
        for span in sorted(spans, key=lambda s: s.start, reverse=True):
            result = result[: span.start] + req.placeholder + result[span.end :]
        return ApplyResult(text=result, removed_count=len(spans))

    def evaluate(self) -> AnonymizerMetrics:
        """Metryki na zbiorze held-out — właściwej miarze jakości detektorów."""
        return evaluate_samples(load_heldout(), self.detect)
