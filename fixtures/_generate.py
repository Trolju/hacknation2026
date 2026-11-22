"""Generator fixtures — deterministyczny.

Uruchomienie:  uv run python fixtures/_generate.py

Wszystkie daty są zakotwiczone na ANCHOR (2026-03-16), żeby demo zawsze
pokazywało właściwe kolory terminów. Aplikacja w trybie demo używa
DEMO_TODAY=2026-03-16 jako "dziś".
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

ANCHOR = date(2026, 3, 16)
ROOT = Path(__file__).resolve().parent


def d(offset: int) -> str:
    return (ANCHOR + timedelta(days=offset)).isoformat()


# ─────────────────────────────── wnioski ────────────────────────────────
CASES = [
    {
        "id": "c0000001-0000-4000-8000-000000000001",
        "case_number": "BKS.IV.1431.1.2026",
        "ordinal": 1,
        "subject": "Wynagrodzenia pracowników Urzędu Miasta w 2025 r.",
        "applicant": "Redakcja Gazety Pomorskiej",
        "inflow_date": d(-24),
        "deadline": d(-10),
        "response_date": None,
        "handler_initials": "JK",
        "status": "zapytania_wyslane",
        "applicant_type": "media",
        "notes": "Wniosek dziennikarski, oczekuje na dane z Wydziału Organizacji i Kadr.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000002",
        "case_number": "BKS.IV.1431.2.2026",
        "ordinal": 2,
        "subject": "Kopie umów najmu lokali komunalnych przy ul. Dworcowej",
        "applicant": "Marta Wiśniewska",
        "inflow_date": d(-14),
        "deadline": d(0),
        "response_date": None,
        "handler_initials": "AM",
        "status": "kwerenda",
        "applicant_type": "osoba_fizyczna",
        "notes": "Wydział Gospodarki Nieruchomościami zgłosił kwerendę — duży wolumen akt.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000003",
        "case_number": "BKS.IV.1431.3.2026",
        "ordinal": 3,
        "subject": "Wydatki na promocję miasta w mediach społecznościowych",
        "applicant": "Stowarzyszenie Obrony Zwierzątek",
        "inflow_date": d(-13),
        "deadline": d(1),
        "response_date": None,
        "handler_initials": "PN",
        "status": "przygotowana_odpowiedz",
        "applicant_type": "organizacja",
        "notes": "Projekt odpowiedzi gotowy, czeka na akceptację kierownika.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000004",
        "case_number": "BKS.IV.1431.4.2026",
        "ordinal": 4,
        "subject": "Protokoły z kontroli Straży Miejskiej w 2025 r.",
        "applicant": "Portal Bydgoszcz24",
        "inflow_date": d(-11),
        "deadline": d(3),
        "response_date": None,
        "handler_initials": "JK",
        "status": "zapytania_wyslane",
        "applicant_type": "media",
        "notes": "",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000005",
        "case_number": "BKS.IV.1431.5.2026",
        "ordinal": 5,
        "subject": "Harmonogram remontów dróg gminnych na 2026 r.",
        "applicant": "Tomasz Grabowski",
        "inflow_date": d(-7),
        "deadline": d(7),
        "response_date": None,
        "handler_initials": "TW",
        "status": "nowy",
        "applicant_type": "osoba_fizyczna",
        "notes": "",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000006",
        "case_number": "BKS.IV.1431.6.2026",
        "ordinal": 6,
        "subject": "Decyzje o warunkach zabudowy wydane w IV kwartale 2025 r.",
        "applicant": "Budowlanka S.A.",
        "inflow_date": d(-6),
        "deadline": d(8),
        "response_date": None,
        "handler_initials": "AM",
        "status": "nowy",
        "applicant_type": "organizacja",
        "notes": "",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000007",
        "case_number": "BKS.IV.1431.7.2026",
        "ordinal": 7,
        "subject": "Umowy z podmiotami zewnętrznymi na utrzymanie zieleni",
        "applicant": "Fundacja Zielone Miasto",
        "inflow_date": d(-34),
        "deadline": d(-20),
        "response_date": d(-21),
        "handler_initials": "PN",
        "status": "odpowiedz_wyslana",
        "applicant_type": "organizacja",
        "notes": "Sprawa zamknięta.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000008",
        "case_number": "BKS.IV.1431.8.2026",
        "ordinal": 8,
        "subject": "Zatrudnienie w jednostkach organizacyjnych miasta",
        "applicant": "Redakcja TV Bydgoszcz",
        "inflow_date": d(-29),
        "deadline": d(-15),
        "response_date": d(-17),
        "handler_initials": "JK",
        "status": "odpowiedz_wyslana",
        "applicant_type": "media",
        "notes": "Sprawa zamknięta.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000009",
        "case_number": "BKS.IV.1431.9.2026",
        "ordinal": 9,
        "subject": "Dostęp do nagrań z monitoringu miejskiego",
        "applicant": "Krzysztof Mazur",
        "inflow_date": d(-5),
        "deadline": d(9),
        "response_date": None,
        "handler_initials": "TW",
        "status": "nowy",
        "applicant_type": "osoba_fizyczna",
        "notes": "Wniosek wymaga oceny prawnej — dane osobowe osób trzecich.",
    },
    {
        "id": "c0000001-0000-4000-8000-000000000010",
        "case_number": "BKS.IV.1431.10.2026",
        "ordinal": 10,
        "subject": "Koszty utrzymania Biura Rady Miasta w 2025 r.",
        "applicant": "Redakcja Radia PiK",
        "inflow_date": d(-4),
        "deadline": d(10),
        "response_date": None,
        "handler_initials": "AM",
        "status": "zapytania_wyslane",
        "applicant_type": "media",
        "notes": "",
    },
]

# ─────────────────────────────── archiwum ───────────────────────────────
# (case_number, subject, year, request, response, departments)
ARCHIVE_RAW = [
    (
        "BKS.IV.1431.87.2025",
        "Wynagrodzenia pracowników Urzędu Miasta w 2024 r.",
        2025,
        "Zwracam się z wnioskiem o udostępnienie informacji publicznej w zakresie wysokości "
        "wynagrodzeń pracowników Urzędu Miasta Bydgoszczy zatrudnionych na stanowiskach "
        "kierowniczych w 2024 roku, wraz ze wskazaniem wysokości premii i nagród rocznych.",
        "W odpowiedzi na wniosek z dnia 12 lutego 2025 r. informuję, że dane dotyczące "
        "wynagrodzeń pracowników samorządowych stanowią informację publiczną w zakresie "
        "wynagrodzeń osób zajmujących kierownicze stanowiska. Zestawienie przygotowano "
        "w podziale na wydziały i biura. Dane osobowe pozostałych pracowników podlegają "
        "ochronie na podstawie art. 5 ust. 2 ustawy o dostępie do informacji publicznej.",
        ["Wydział Organizacji i Kadr", "Wydział Budżetu i Księgowości"],
    ),
    (
        "BKS.IV.1431.112.2025",
        "Nagrody i premie dla kierowników jednostek organizacyjnych",
        2025,
        "Proszę o udostępnienie wykazu nagród i premii przyznanych w 2024 roku kierownikom "
        "jednostek organizacyjnych miasta, z podaniem kwot i uzasadnienia przyznania.",
        "Informuję, że wykaz nagród i premii przyznanych kierownikom jednostek "
        "organizacyjnych w 2024 roku obejmuje łącznie 34 osoby. Łączna kwota przyznanych "
        "nagród wyniosła 412 000 zł. Szczegółowe uzasadnienia stanowią dokumenty wewnętrzne "
        "i nie podlegają udostępnieniu.",
        ["Wydział Organizacji i Kadr"],
    ),
    (
        "BKS.IV.1431.64.2025",
        "Zatrudnienie w Urzędzie Miasta w latach 2023-2024",
        2025,
        "Wnoszę o udostępnienie informacji o liczbie etatów w Urzędzie Miasta Bydgoszczy "
        "na koniec 2023 i 2024 roku, z podziałem na wydziały.",
        "Według stanu na 31 grudnia 2024 r. Urząd Miasta Bydgoszczy zatrudniał 1 247 osób, "
        "co odpowiadało 1 198,5 etatu. W analogicznym okresie 2023 r. zatrudnienie wynosiło "
        "1 231 osób (1 184,25 etatu). Zestawienie w podziale na komórki organizacyjne "
        "stanowi załącznik do niniejszej odpowiedzi.",
        ["Wydział Organizacji i Kadr"],
    ),
    (
        "BKS.IV.1431.201.2025",
        "Umowy najmu lokali komunalnych w Śródmieściu",
        2025,
        "Zwracam się o udostępnienie kopii umów najmu lokali komunalnych położonych "
        "w rejonie Śródmieścia, zawartych w 2024 roku, wraz z wysokością czynszu.",
        "Informuję, że gmina posiada 2 843 lokale komunalne. W 2024 roku zawarto 186 umów "
        "najmu. Kopie umów zawierają dane osobowe najemców i nie podlegają udostępnieniu "
        "w całości. Udostępniono zestawienie zbiorcze: liczbę umów, średnią powierzchnię "
        "lokalu oraz średnią stawkę czynszu (11,42 zł/m²).",
        ["Wydział Gospodarki Nieruchomościami"],
    ),
    (
        "BKS.IV.1431.178.2025",
        "Zaległości czynszowe w lokalach komunalnych",
        2025,
        "Proszę o podanie łącznej kwoty zaległości czynszowych w lokalach komunalnych "
        "na koniec 2024 roku oraz liczby postępowań windykacyjnych.",
        "Łączna kwota zaległości czynszowych w lokalach komunalnych na dzień 31 grudnia "
        "2024 r. wyniosła 18 734 512,88 zł. W 2024 roku wszczęto 412 postępowań "
        "windykacyjnych, z czego 87 zakończyło się skierowaniem sprawy do sądu.",
        ["Wydział Gospodarki Nieruchomościami", "Wydział Budżetu i Księgowości"],
    ),
    (
        "BKS.IV.1431.95.2025",
        "Wykaz lokali socjalnych i ich stan techniczny",
        2025,
        "Wnoszę o udostępnienie wykazu lokali socjalnych będących w zasobie miasta wraz "
        "z informacją o ich stanie technicznym.",
        "Gmina dysponuje 318 lokalami socjalnymi. 41 lokali wymaga remontu kapitalnego, "
        "112 remontu bieżącego. Wykaz adresowy wraz z oceną stanu technicznego stanowi "
        "załącznik do odpowiedzi.",
        ["Wydział Gospodarki Nieruchomościami", "Wydział Gospodarki Komunalnej"],
    ),
    (
        "BKS.IV.1431.33.2025",
        "Wydatki na promocję miasta w mediach społecznościowych w 2024 r.",
        2025,
        "Proszę o udostępnienie informacji o wydatkach poniesionych przez miasto na "
        "promocję w mediach społecznościowych w 2024 roku, z podziałem na platformy "
        "i wykonawców.",
        "W 2024 roku miasto wydatkowało na promocję w mediach społecznościowych "
        "1 284 700 zł. Podział: Facebook 486 200 zł, Instagram 312 400 zł, LinkedIn "
        "98 100 zł, YouTube 188 000 zł, pozostałe 200 000 zł. Wykaz wykonawców wraz "
        "z numerami umów stanowi załącznik.",
        ["Wydział Promocji Miasta", "Biuro Komunikacji Społecznej"],
    ),
    (
        "BKS.IV.1431.141.2025",
        "Kampanie reklamowe miasta i ich efekty",
        2025,
        "Zwracam się o udostępnienie informacji o kampaniach reklamowych miasta "
        "zrealizowanych w 2024 roku wraz z ich budżetami i miernikami efektywności.",
        "W 2024 roku zrealizowano 14 kampanii reklamowych o łącznym budżecie "
        "3 847 200 zł. Największe: kampania wizerunkowa (1 240 000 zł), kampania "
        "inwestycyjna (890 000 zł), kampania turystyczna (612 000 zł). Mierniki "
        "efektywności obejmowały zasięg, liczbę odsłon i współczynnik konwersji.",
        ["Wydział Promocji Miasta"],
    ),
    (
        "BKS.IV.1431.19.2025",
        "Umowy z agencjami marketingowymi",
        2025,
        "Proszę o wykaz umów zawartych przez miasto z agencjami marketingowymi "
        "w latach 2023-2024 wraz z wartościami.",
        "W latach 2023-2024 miasto zawarło 9 umów z agencjami marketingowymi o łącznej "
        "wartości 4 128 900 zł. Wykaz obejmuje nazwy wykonawców, daty zawarcia, wartości "
        "oraz przedmiot umowy. Treść umów udostępniono w zakresie niezawierającym "
        "tajemnicy przedsiębiorstwa.",
        ["Wydział Promocji Miasta", "Wydział Zamówień Publicznych"],
    ),
    (
        "BKS.IV.1431.76.2025",
        "Protokoły kontroli Straży Miejskiej w 2024 r.",
        2025,
        "Wnoszę o udostępnienie protokołów z kontroli przeprowadzonych przez Straż Miejską "
        "w 2024 roku wraz z liczbą nałożonych mandatów.",
        "Straż Miejska przeprowadziła w 2024 roku 1 842 interwencje kontrolne. Nałożono "
        "6 218 mandatów na łączną kwotę 1 487 300 zł. Protokoły kontroli udostępniono "
        "w zakresie wyłączającym dane osobowe osób kontrolowanych oraz informacje "
        "o czynnościach operacyjno-rozpoznawczych.",
        ["Straż Miejska"],
    ),
    (
        "BKS.IV.1431.158.2025",
        "Statystyki interwencji Straży Miejskiej",
        2025,
        "Proszę o dane statystyczne dotyczące interwencji Straży Miejskiej w latach "
        "2023-2024 z podziałem na kategorie zgłoszeń.",
        "W 2024 roku przyjęto 28 412 zgłoszeń. Kategorie: zakłócanie porządku 9 218, "
        "sprawy drogowe 6 104, spożywanie alkoholu 4 872, zwierzęta 3 218, pozostałe "
        "5 000. W 2023 roku łącznie 26 890 zgłoszeń.",
        ["Straż Miejska"],
    ),
    (
        "BKS.IV.1431.44.2025",
        "Kontrole pojazdów przewożących odpady",
        2025,
        "Zwracam się o informację o liczbie kontroli pojazdów przewożących odpady "
        "przeprowadzonych przez Straż Miejską w 2024 roku.",
        "W 2024 roku przeprowadzono 214 kontroli pojazdów przewożących odpady. "
        "Stwierdzono 38 nieprawidłowości, nałożono 22 mandaty na łączną kwotę 41 200 zł. "
        "Skierowano 6 wniosków do sądu.",
        ["Straż Miejska", "Wydział Gospodarki Komunalnej"],
    ),
    (
        "BKS.IV.1431.52.2025",
        "Harmonogram remontów dróg gminnych na 2025 r.",
        2025,
        "Proszę o udostępnienie harmonogramu remontów dróg gminnych zaplanowanych "
        "na 2025 rok wraz z szacowanymi kosztami.",
        "Harmonogram remontów dróg gminnych na 2025 rok obejmuje 47 zadań o łącznym "
        "budżecie 68 420 000 zł. Największe zadania: przebudowa ul. Fordońskiej "
        "(18 200 000 zł), remont ul. Gdańskiej (12 400 000 zł), modernizacja ul. "
        "Nakielskiej (9 800 000 zł). Szczegółowy harmonogram stanowi załącznik.",
        ["Zarząd Dróg Miejskich i Komunikacji Publicznej", "Wydział Transportu i Dróg"],
    ),
    (
        "BKS.IV.1431.133.2025",
        "Stan techniczny mostów i wiaduktów",
        2025,
        "Wnoszę o udostępnienie informacji o stanie technicznym mostów i wiaduktów "
        "będących w zarządzie miasta.",
        "Miasto zarządza 38 obiektami mostowymi. Stan dobry: 21, dostateczny: 12, "
        "wymagający remontu: 5. Ostatnie przeglądy przeprowadzono w 2024 roku. "
        "Wykaz obiektów wraz z oceną stanu technicznego stanowi załącznik.",
        ["Zarząd Dróg Miejskich i Komunikacji Publicznej"],
    ),
    (
        "BKS.IV.1431.8.2025",
        "Remonty chodników i ścieżek rowerowych",
        2025,
        "Proszę o wykaz remontów chodników i ścieżek rowerowych zrealizowanych "
        "w 2024 roku.",
        "W 2024 roku zrealizowano 62 remonty chodników (łączna długość 18,4 km) oraz "
        "14 odcinków ścieżek rowerowych (łączna długość 9,2 km). Łączny koszt wyniósł "
        "24 180 000 zł.",
        ["Zarząd Dróg Miejskich i Komunikacji Publicznej"],
    ),
    (
        "BKS.IV.1431.167.2025",
        "Decyzje o warunkach zabudowy wydane w III kwartale 2025 r.",
        2025,
        "Zwracam się o udostępnienie wykazu decyzji o warunkach zabudowy wydanych "
        "w III kwartale 2025 roku wraz z lokalizacjami inwestycji.",
        "W III kwartale 2025 roku wydano 214 decyzji o warunkach zabudowy, w tym 187 "
        "pozytywnych i 27 odmownych. Wykaz obejmuje oznaczenia nieruchomości, rodzaj "
        "inwestycji i datę wydania decyzji. Dane wnioskodawców podlegają ochronie.",
        ["Wydział Architektury i Urbanistyki"],
    ),
    (
        "BKS.IV.1431.88.2025",
        "Pozwolenia na budowę wydane w 2024 r.",
        2025,
        "Proszę o dane o liczbie pozwoleń na budowę wydanych w 2024 roku z podziałem "
        "na rodzaje inwestycji.",
        "W 2024 roku wydano 486 pozwoleń na budowę: budynki mieszkalne jednorodzinne 218, "
        "budynki wielorodzinne 42, budynki usługowe 96, infrastruktura techniczna 130. "
        "Łączna powierzchnia użytkowa objęta pozwoleniami: 412 800 m².",
        ["Wydział Architektury i Urbanistyki"],
    ),
    (
        "BKS.IV.1431.23.2025",
        "Miejscowe plany zagospodarowania przestrzennego",
        2025,
        "Wnoszę o wykaz miejscowych planów zagospodarowania przestrzennego uchwalonych "
        "w latach 2023-2024.",
        "W latach 2023-2024 uchwalono 11 miejscowych planów zagospodarowania "
        "przestrzennego obejmujących łącznie 284 ha. Wykaz wraz z numerami uchwał "
        "i powierzchniami stanowi załącznik.",
        ["Wydział Architektury i Urbanistyki"],
    ),
    (
        "BKS.IV.1431.71.2025",
        "Umowy na utrzymanie zieleni miejskiej",
        2025,
        "Proszę o udostępnienie wykazu umów zawartych na utrzymanie zieleni miejskiej "
        "w 2024 roku wraz z wartościami i zakresem prac.",
        "W 2024 roku obowiązywały 4 umowy na utrzymanie zieleni miejskiej o łącznej "
        "wartości 12 840 000 zł. Zakres obejmował pielęgnację 1 842 ha terenów zieleni, "
        "utrzymanie 68 400 drzew oraz nasadzenia 2 100 sztuk.",
        ["Wydział Gospodarki Komunalnej"],
    ),
    (
        "BKS.IV.1431.149.2025",
        "Wycinka drzew w 2024 r. i nasadzenia zastępcze",
        2025,
        "Zwracam się o dane o liczbie wydanych zezwoleń na wycinkę drzew w 2024 roku "
        "oraz o liczbie nasadzeń zastępczych.",
        "W 2024 roku wydano 1 284 zezwolenia na wycinkę 3 412 drzew. Wykonano 4 218 "
        "nasadzeń zastępczych. Wpływy z opłat za usunięcie drzew wyniosły 1 842 300 zł.",
        ["Wydział Ochrony Środowiska"],
    ),
    (
        "BKS.IV.1431.12.2025",
        "Koszty utrzymania parków miejskich",
        2025,
        "Proszę o informację o kosztach utrzymania parków miejskich w 2024 roku.",
        "Koszty utrzymania 42 parków miejskich w 2024 roku wyniosły 8 412 000 zł, "
        "w tym pielęgnacja 5 218 000 zł, nawadnianie 1 284 000 zł, mała architektura "
        "1 910 000 zł.",
        ["Wydział Gospodarki Komunalnej"],
    ),
    (
        "BKS.IV.1431.56.2025",
        "Zatrudnienie w jednostkach organizacyjnych miasta",
        2025,
        "Wnoszę o udostępnienie danych o zatrudnieniu w jednostkach organizacyjnych "
        "miasta na koniec 2024 roku.",
        "Na koniec 2024 roku jednostki organizacyjne miasta zatrudniały łącznie 8 412 "
        "osób (7 986,25 etatu). Największe jednostki: Miejski Ośrodek Pomocy Społecznej "
        "(842 osoby), Zarząd Dróg Miejskich (486 osób), szkoły i przedszkola (4 218 osób).",
        ["Wydział Organizacji i Kadr", "Wydział Edukacji"],
    ),
    (
        "BKS.IV.1431.104.2025",
        "Wynagrodzenia w jednostkach organizacyjnych",
        2025,
        "Proszę o dane o przeciętnym wynagrodzeniu w jednostkach organizacyjnych "
        "miasta w 2024 roku.",
        "Przeciętne miesięczne wynagrodzenie brutto w jednostkach organizacyjnych miasta "
        "w 2024 roku wyniosło 6 842,18 zł. Najwyższe w jednostkach oświatowych "
        "(7 218,40 zł), najniższe w jednostkach pomocy społecznej (5 984,12 zł).",
        ["Wydział Organizacji i Kadr"],
    ),
    (
        "BKS.IV.1431.189.2025",
        "Dostęp do nagrań z monitoringu miejskiego",
        2025,
        "Zwracam się o udostępnienie nagrań z monitoringu miejskiego z rejonu "
        "ul. Mostowej z dnia 14 listopada 2025 r. w godzinach 22:00-24:00.",
        "Informuję, że nagrania z monitoringu miejskiego nie stanowią informacji "
        "publicznej w rozumieniu ustawy, ponieważ zawierają dane osobowe osób "
        "trzecich, a ich udostępnienie wymagałoby przetwarzania danych w sposób "
        "nieproporcjonalny do celu. Wniosek przekazano do rozpatrzenia w trybie "
        "art. 5 ust. 2 ustawy.",
        ["Straż Miejska", "Biuro Prawne"],
    ),
    (
        "BKS.IV.1431.62.2025",
        "Lokalizacja kamer monitoringu miejskiego",
        2025,
        "Proszę o wykaz lokalizacji kamer monitoringu miejskiego wraz z ich typem.",
        "System monitoringu miejskiego obejmuje 486 kamer w 214 lokalizacjach. "
        "Kamery stałe: 412, kamery obrotowe: 74. Wykaz lokalizacji na poziomie ulic "
        "stanowi załącznik. Szczegółowe parametry techniczne objęte są klauzulą "
        "bezpieczeństwa.",
        ["Straż Miejska", "Wydział Informatyki"],
    ),
    (
        "BKS.IV.1431.117.2025",
        "Koszty funkcjonowania monitoringu miejskiego",
        2025,
        "Wnoszę o informację o kosztach funkcjonowania monitoringu miejskiego w 2024 r.",
        "Koszty funkcjonowania monitoringu miejskiego w 2024 roku wyniosły 4 218 000 zł, "
        "w tym utrzymanie infrastruktury 2 184 000 zł, obsługa centrum monitoringu "
        "1 642 000 zł, modernizacja 392 000 zł.",
        ["Straż Miejska", "Wydział Informatyki"],
    ),
    (
        "BKS.IV.1431.41.2025",
        "Koszty utrzymania Biura Rady Miasta",
        2025,
        "Proszę o udostępnienie informacji o kosztach utrzymania Biura Rady Miasta "
        "w 2024 roku.",
        "Koszty utrzymania Biura Rady Miasta w 2024 roku wyniosły 3 842 000 zł, w tym "
        "wynagrodzenia 2 918 000 zł, obsługa posiedzeń 486 000 zł, diety radnych "
        "1 842 000 zł (ujęte odrębnie), materiały i usługi 438 000 zł.",
        ["Biuro Rady Miasta", "Wydział Budżetu i Księgowości"],
    ),
    (
        "BKS.IV.1431.98.2025",
        "Diety i wydatki radnych",
        2025,
        "Zwracam się o wykaz diet pobranych przez radnych w 2024 roku.",
        "Łączna kwota diet wypłaconych radnym w 2024 roku wyniosła 1 842 000 zł. "
        "Wykaz obejmuje kwoty diet w podziale na radnych, bez danych adresowych. "
        "Średnia dieta miesięczna wyniosła 2 842 zł.",
        ["Biuro Rady Miasta"],
    ),
    (
        "BKS.IV.1431.7.2025",
        "Transmisje i protokoły sesji Rady Miasta",
        2025,
        "Proszę o informację o kosztach transmisji sesji Rady Miasta w 2024 roku.",
        "Koszty transmisji i archiwizacji sesji Rady Miasta w 2024 roku wyniosły "
        "184 200 zł. Zrealizowano 24 sesje, wszystkie transmitowane online. "
        "Protokoły są publikowane w BIP.",
        ["Biuro Rady Miasta", "Wydział Informatyki"],
    ),
    (
        "BKS.IV.1431.126.2025",
        "Dotacje dla organizacji pozarządowych",
        2025,
        "Wnoszę o udostępnienie wykazu dotacji udzielonych organizacjom pozarządowym "
        "w 2024 roku.",
        "W 2024 roku udzielono 284 dotacji organizacjom pozarządowym na łączną kwotę "
        "18 420 000 zł. Największe obszary: sport 6 218 000 zł, kultura 4 842 000 zł, "
        "pomoc społeczna 3 918 000 zł. Wykaz beneficjentów i kwot stanowi załącznik.",
        ["Wydział Polityki Społecznej", "Wydział Kultury i Sportu"],
    ),
    (
        "BKS.IV.1431.83.2025",
        "Wydatki na kulturę i imprezy masowe",
        2025,
        "Proszę o informację o wydatkach miasta na imprezy kulturalne w 2024 roku.",
        "Wydatki na imprezy kulturalne w 2024 roku wyniosły 12 840 000 zł. "
        "Zrealizowano 142 wydarzenia, w których uczestniczyło łącznie 486 000 osób. "
        "Największe: festiwal muzyczny (2 840 000 zł), obchody święta miasta "
        "(1 918 000 zł).",
        ["Wydział Kultury i Sportu"],
    ),
    (
        "BKS.IV.1431.172.2025",
        "Wydatki na sport i infrastrukturę sportową",
        2025,
        "Wnoszę o dane o wydatkach na sport w 2024 roku wraz z wykazem inwestycji.",
        "Wydatki na sport w 2024 roku wyniosły 24 180 000 zł, w tym dotacje dla klubów "
        "8 412 000 zł, inwestycje 14 218 000 zł, imprezy 1 550 000 zł. Zrealizowano "
        "6 inwestycji sportowych.",
        ["Wydział Kultury i Sportu"],
    ),
    (
        "BKS.IV.1431.29.2025",
        "Zamówienia publiczne udzielone w trybie z wolnej ręki",
        2025,
        "Proszę o wykaz zamówień publicznych udzielonych w trybie z wolnej ręki "
        "w 2024 roku.",
        "W 2024 roku udzielono 42 zamówień w trybie z wolnej ręki na łączną kwotę "
        "28 412 000 zł, co stanowiło 8,4% wartości wszystkich zamówień. Wykaz wraz "
        "z uzasadnieniem wyboru trybu stanowi załącznik.",
        ["Wydział Zamówień Publicznych"],
    ),
    (
        "BKS.IV.1431.154.2025",
        "Wartość zamówień publicznych w 2024 r.",
        2025,
        "Zwracam się o łączną wartość zamówień publicznych udzielonych przez miasto "
        "w 2024 roku.",
        "Łączna wartość zamówień publicznych udzielonych w 2024 roku wyniosła "
        "338 214 000 zł, w tym w trybie przetargu nieograniczonego 284 918 000 zł. "
        "Liczba postępowań: 486.",
        ["Wydział Zamówień Publicznych"],
    ),
    (
        "BKS.IV.1431.36.2025",
        "Jakość powietrza i działania antysmogowe",
        2025,
        "Proszę o informację o działaniach miasta na rzecz poprawy jakości powietrza "
        "w 2024 roku.",
        "W 2024 roku zrealizowano program wymiany 842 pieców (dotacja 4 218 000 zł), "
        "przeprowadzono 1 284 kontroli palenisk, nałożono 86 mandatów. Stężenie PM10 "
        "spadło o 12% względem 2023 roku.",
        ["Wydział Ochrony Środowiska", "Straż Miejska"],
    ),
    (
        "BKS.IV.1431.108.2025",
        "Gospodarka odpadami komunalnymi",
        2025,
        "Wnoszę o dane o kosztach i efektach gospodarki odpadami komunalnymi w 2024 r.",
        "W 2024 roku zebrano 142 800 ton odpadów komunalnych. Koszt systemu wyniósł "
        "84 218 000 zł. Poziom recyklingu osiągnął 38,4%. Stawka opłaty śmieciowej "
        "wynosiła 32,40 zł od osoby.",
        ["Wydział Gospodarki Komunalnej"],
    ),
    (
        "BKS.IV.1431.195.2025",
        "Transport publiczny — koszty i finansowanie",
        2025,
        "Proszę o informację o kosztach funkcjonowania transportu publicznego "
        "w 2024 roku.",
        "Koszty funkcjonowania transportu publicznego w 2024 roku wyniosły "
        "218 412 000 zł, z czego dopłata miasta 142 218 000 zł. Przewieziono "
        "84,2 mln pasażerów. Liczba linii: 68.",
        ["Zarząd Dróg Miejskich i Komunikacji Publicznej", "Wydział Transportu i Dróg"],
    ),
    (
        "BKS.IV.1431.14.2025",
        "Edukacja — liczba uczniów i nauczycieli",
        2025,
        "Zwracam się o dane o liczbie uczniów i nauczycieli w placówkach oświatowych "
        "prowadzonych przez miasto.",
        "W roku szkolnym 2024/2025 do placówek prowadzonych przez miasto uczęszczało "
        "42 184 uczniów. Zatrudnionych było 6 842 nauczycieli (5 918,42 etatu). "
        "Liczba placówek: 142.",
        ["Wydział Edukacji"],
    ),
    (
        "BKS.IV.1431.47.2025",
        "Remonty placówek oświatowych",
        2025,
        "Proszę o wykaz remontów zrealizowanych w placówkach oświatowych w 2024 roku.",
        "W 2024 roku zrealizowano 84 remonty w placówkach oświatowych na łączną kwotę "
        "28 412 000 zł. Największe: termomodernizacja SP nr 12 (6 218 000 zł), "
        "modernizacja kuchni w Przedszkolu nr 34 (1 842 000 zł).",
        ["Wydział Edukacji", "Wydział Inwestycji"],
    ),
    (
        "BKS.IV.1431.181.2025",
        "Pomoc społeczna — świadczenia i beneficjenci",
        2025,
        "Wnoszę o dane o świadczeniach pomocy społecznej udzielonych w 2024 roku.",
        "W 2024 roku z pomocy społecznej skorzystało 18 412 osób. Łączna kwota "
        "świadczeń wyniosła 84 218 000 zł. Dominujące formy: zasiłki okresowe "
        "(42 184 000 zł), posiłki (12 842 000 zł), schronienie (8 412 000 zł).",
        ["Wydział Polityki Społecznej", "Miejski Ośrodek Pomocy Społecznej"],
    ),
    (
        "BKS.IV.1431.3.2025",
        "Dostępność architektoniczna budynków urzędu",
        2025,
        "Proszę o informację o dostosowaniu budynków urzędu do potrzeb osób "
        "z niepełnosprawnościami.",
        "Spośród 18 budynków urzędu 12 jest w pełni dostosowanych (podjazdy, windy, "
        "toalety). 4 wymagają modernizacji, 2 są niedostosowane. Plan dostosowania "
        "obejmuje lata 2025-2027 z budżetem 4 218 000 zł.",
        ["Wydział Administracyjny", "Wydział Inwestycji"],
    ),
    (
        "BKS.IV.1431.91.2025",
        "Rejestr umów cywilnoprawnych",
        2025,
        "Zwracam się o wykaz umów cywilnoprawnych zawartych przez urząd w 2024 roku.",
        "W 2024 roku zawarto 284 umowy cywilnoprawne o łącznej wartości 8 412 000 zł. "
        "Wykaz obejmuje przedmiot umowy, wartość i datę zawarcia. Dane osobowe "
        "wykonawców będących osobami fizycznymi podlegały anonimizacji.",
        ["Wydział Organizacji i Kadr", "Biuro Prawne"],
    ),
    (
        "BKS.IV.1431.68.2025",
        "Skargi i wnioski obywatelskie w 2024 r.",
        2025,
        "Proszę o dane o liczbie skarg i wniosków złożonych do urzędu w 2024 roku.",
        "W 2024 roku złożono 1 842 skargi i 486 wniosków. Uwzględniono 412 skarg "
        "(22,4%), 1 218 uznano za bezzasadne, 212 pozostawiono bez rozpatrzenia. "
        "Średni czas rozpatrzenia: 24 dni.",
        ["Biuro Rady Miasta", "Wydział Organizacji i Kadr"],
    ),
    (
        "BKS.IV.1431.122.2025",
        "Czas rozpatrywania wniosków UDIP",
        2025,
        "Wnoszę o dane o średnim czasie rozpatrywania wniosków o dostęp do informacji "
        "publicznej w 2024 roku.",
        "W 2024 roku wpłynęło 1 284 wniosków UDIP. Średni czas odpowiedzi wyniósł "
        "11,4 dnia. W terminie 14 dni odpowiedziano na 1 142 wnioski (88,9%). "
        "W 86 przypadkach przedłużono termin, w 56 nie dotrzymano terminu.",
        ["Biuro Komunikacji Społecznej", "Biuro Prawne"],
    ),
    (
        "BKS.IV.1431.137.2025",
        "Odmowy udostępnienia informacji publicznej",
        2025,
        "Proszę o wykaz decyzji odmownych wydanych w sprawach UDIP w 2024 roku "
        "wraz z podstawami prawnymi.",
        "W 2024 roku wydano 84 decyzje odmowne. Podstawy: ochrona danych osobowych "
        "(42), tajemnica przedsiębiorstwa (18), informacja przetworzona (14), "
        "inne (10). Od 22 decyzji złożono skargi do WSA.",
        ["Biuro Prawne"],
    ),
    (
        "BKS.IV.1431.58.2025",
        "Wydatki na reprezentację i spotkania",
        2025,
        "Zwracam się o informację o wydatkach na reprezentację w 2024 roku.",
        "Wydatki na reprezentację w 2024 roku wyniosły 284 200 zł, w tym poczęstunki "
        "na spotkaniach 142 800 zł, upominki promocyjne 98 400 zł, pozostałe 43 000 zł. "
        "Wydatki poniesiono zgodnie z zarządzeniem nr 536/2024.",
        ["Wydział Budżetu i Księgowości", "Wydział Promocji Miasta"],
    ),
    (
        "BKS.IV.1431.164.2025",
        "Flota samochodowa urzędu",
        2025,
        "Proszę o wykaz pojazdów służbowych będących w dyspozycji urzędu wraz "
        "z kosztami utrzymania.",
        "Urząd dysponuje 42 pojazdami służbowymi. Koszty utrzymania w 2024 roku "
        "wyniosły 1 842 000 zł, w tym paliwo 842 000 zł, serwis 486 000 zł, "
        "ubezpieczenia 214 000 zł, leasing 300 000 zł.",
        ["Wydział Administracyjny"],
    ),
    (
        "BKS.IV.1431.26.2025",
        "Inwestycje miejskie — stan realizacji",
        2025,
        "Wnoszę o wykaz inwestycji miejskich w realizacji na koniec 2024 roku.",
        "Na koniec 2024 roku w realizacji było 84 inwestycje o łącznej wartości "
        "486 218 000 zł. Zakończono 42 inwestycje. Największe: budowa linii "
        "tramwajowej (142 000 000 zł), modernizacja oczyszczalni (84 000 000 zł).",
        ["Wydział Inwestycji"],
    ),
    (
        "BKS.IV.1431.199.2025",
        "Dług publiczny miasta",
        2025,
        "Proszę o informację o zadłużeniu miasta na koniec 2024 roku.",
        "Zadłużenie miasta na koniec 2024 roku wyniosło 842 218 000 zł, co stanowiło "
        "38,4% dochodów. Obsługa długu kosztowała 28 412 000 zł. Rating miasta: A- "
        "stabilny.",
        ["Wydział Budżetu i Księgowości", "Skarbnik Miasta"],
    ),
]


def build_archive() -> list[dict]:
    out = []
    for i, (num, subject, year, req, resp, deps) in enumerate(ARCHIVE_RAW, start=1):
        out.append(
            {
                "archive_id": f"a{i:04d}",
                "case_number": num,
                "subject": subject,
                "year": year,
                "request_text": req,
                "response_text": resp,
                "departments": deps,
            }
        )
    return out


# ────────────────────────────── wydziały ────────────────────────────────
DEPARTMENTS = [
    ("waiu", "Wydział Architektury i Urbanistyki", "wydzial",
     ["warunki zabudowy", "pozwolenie na budowę", "plan miejscowy", "zagospodarowanie przestrzenne", "architektura", "urbanistyka", "inwestycja budowlana"]),
    ("wbiu", "Wydział Budżetu i Księgowości", "wydzial",
     ["budżet", "księgowość", "wydatki", "dochody", "zadłużenie", "reprezentacja", "faktury", "płatności"]),
    ("wedu", "Wydział Edukacji", "wydzial",
     ["szkoła", "przedszkole", "uczniowie", "nauczyciele", "oświata", "edukacja", "placówka oświatowa"]),
    ("wfin", "Wydział Finansów", "wydzial",
     ["finanse", "podatki lokalne", "opłaty", "windykacja", "budżet miasta"]),
    ("wgik", "Wydział Geodezji i Katastru", "wydzial",
     ["geodezja", "kataster", "działka", "ewidencja gruntów", "mapa", "granice nieruchomości"]),
    ("wgk", "Wydział Gospodarki Komunalnej", "wydzial",
     ["odpady", "zielen", "park", "utrzymanie miasta", "komunalny", "woda", "kanalizacja", "czystość"]),
    ("wgn", "Wydział Gospodarki Nieruchomościami", "wydzial",
     ["lokal komunalny", "najem", "czynsz", "nieruchomość", "sprzedaż działki", "dzierżawa", "zasób komunalny"]),
    ("winf", "Wydział Informatyki", "wydzial",
     ["informatyka", "system", "monitoring", "sieć", "oprogramowanie", "dane", "cyfryzacja"]),
    ("winw", "Wydział Inwestycji", "wydzial",
     ["inwestycja", "remont", "budowa", "modernizacja", "termomodernizacja", "przetarg inwestycyjny"]),
    ("wks", "Wydział Kultury i Sportu", "wydzial",
     ["kultura", "sport", "impreza", "festiwal", "klub sportowy", "wydarzenie kulturalne", "dotacja kulturalna"]),
    ("wos", "Wydział Ochrony Środowiska", "wydzial",
     ["środowisko", "wycinka", "drzewo", "powietrze", "smog", "ekologia", "zwierzęta", "hałas"]),
    ("wok", "Wydział Organizacji i Kadr", "wydzial",
     ["wynagrodzenie", "zatrudnienie", "etat", "kadry", "nabór", "umowa cywilnoprawna", "nagroda", "premia"]),
    ("wps", "Wydział Polityki Społecznej", "wydzial",
     ["pomoc społeczna", "zasiłek", "świadczenie", "organizacja pozarządowa", "dotacja", "senior", "niepełnosprawność"]),
    ("wpm", "Wydział Promocji Miasta", "wydzial",
     ["promocja", "reklama", "kampania", "media społecznościowe", "marketing", "wizerunek", "upominek"]),
    ("wrm", "Wydział Rozwoju Miasta", "wydzial",
     ["rozwój", "strategia", "projekt unijny", "fundusze europejskie", "rewitalizacja"]),
    ("wso", "Wydział Spraw Obywatelskich", "wydzial",
     ["ewidencja ludności", "dowód osobisty", "meldunek", "akt stanu cywilnego", "obywatelstwo"]),
    ("wtd", "Wydział Transportu i Dróg", "wydzial",
     ["droga", "transport", "komunikacja publiczna", "chodnik", "ścieżka rowerowa", "parkowanie", "most"]),
    ("wzp", "Wydział Zamówień Publicznych", "wydzial",
     ["zamówienie publiczne", "przetarg", "wolna ręka", "specyfikacja", "oferta", "umowa ramowa"]),
    ("bks", "Biuro Komunikacji Społecznej", "biuro",
     ["komunikacja", "rzecznik", "informacja publiczna", "wniosek UDIP", "kontakt z mediami"]),
    ("brm", "Biuro Rady Miasta", "biuro",
     ["rada miasta", "radny", "sesja", "dieta", "uchwała", "protokół sesji", "komisja"]),
    ("bpra", "Biuro Prawne", "biuro",
     ["opinia prawna", "decyzja", "odmowa", "skarga", "sąd", "postępowanie administracyjne"]),
    ("bzk", "Biuro Zarządzania Kryzysowego", "biuro",
     ["kryzys", "zagrożenie", "powódź", "ewakuacja", "alarm", "bezpieczeństwo"]),
    ("sm", "Straż Miejska", "biuro",
     ["straż miejska", "interwencja", "mandat", "kontrola", "monitoring", "patrol", "wykroczenie"]),
    ("zdm", "Zarząd Dróg Miejskich i Komunikacji Publicznej", "biuro",
     ["droga", "remont drogi", "most", "wiadukt", "transport publiczny", "tramwaj", "autobus", "przystanek"]),
    ("wadm", "Wydział Administracyjny", "wydzial",
     ["administracja", "budynek urzędu", "pojazd służbowy", "flota", "dostawa", "majątek"]),
    ("wzd", "Wydział Zdrowia", "wydzial",
     ["zdrowie", "przychodnia", "profilaktyka", "szczepienie", "placówka medyczna"]),
]


def build_departments() -> list[dict]:
    return [
        {
            "id": did,
            "name": name,
            "kind": kind,
            "keywords": kws,
            "url": "https://bip.um.bydgoszcz.pl/artykuly/198/wydzialy",
        }
        for did, name, kind, kws in DEPARTMENTS
    ]


# ─────────────────────────────── ustawy ────────────────────────────────
UDIP_TEXT = """\
USTAWA z dnia 6 września 2001 r. o dostępie do informacji publicznej
(wyciąg przygotowany na potrzeby prototypu — nie stanowi tekstu jednolitego)

Art. 1. 1. Każdemu przysługuje, bez konieczności wykazania interesu prawnego lub
faktycznego, prawo dostępu do informacji publicznej.
2. Informacją publiczną jest każda informacja o sprawach publicznych.

Art. 2. 1. Każdemu przysługuje prawo dostępu do informacji publicznej, jeżeli
informacja taka nie została udostępniona w trybie określonym w art. 5 ust. 1.

Art. 3. 1. Prawo do informacji publicznej obejmuje uprawnienia do:
1) uzyskania informacji publicznej, w tym uzyskania informacji przetworzonej
   w takim zakresie, w jakim jest to szczególnie istotne dla interesu publicznego;
2) wglądu do dokumentów urzędowych;
3) dostępu do posiedzeń kolegialnych organów władzy publicznej.

Art. 4. 1. Obowiązane do udostępniania informacji publicznej są władze publiczne
oraz inne podmioty wykonujące zadania publiczne.

Art. 5. 1. Prawo do informacji publicznej podlega ograniczeniu w zakresie i na
zasadach określonych w przepisach o ochronie informacji niejawnych oraz o ochronie
innych tajemnic ustawowo chronionych.
2. Prawo do informacji publicznej podlega ograniczeniu ze względu na prywatność
osoby fizycznej. Ograniczenie nie może dotyczyć informacji o osobach pełniących
funkcje publiczne, mających związek z pełnieniem tych funkcji.

Art. 6. 1. Udostępnianie informacji publicznej odbywa się przez:
1) ogłaszanie informacji publicznych, w tym dokumentów urzędowych, w Biuletynie
   Informacji Publicznej;
2) udostępnianie na wniosek;
3) wyłożenie lub wywieszenie w miejscach ogólnie dostępnych;
4) udostępnianie w drodze posiedzeń organów kolegialnych.

Art. 10. 1. Informacja publiczna, która nie została udostępniona w Biuletynie
Informacji Publicznej, jest udostępniana na wniosek.
2. Informacja publiczna, która może być niezwłocznie udostępniona, jest
udostępniana w formie ustnej lub pisemnej bez pisemnego wniosku.

Art. 13. 1. Udostępnianie informacji publicznej na wniosek następuje bez zbędnej
zwłoki, nie później jednak niż w terminie 14 dni od dnia złożenia wniosku.
2. Jeżeli informacja publiczna nie może być udostępniona w terminie określonym
w ust. 1, podmiot obowiązany do jej udostępnienia powiadamia w tym terminie
wnioskodawcę o przyczynach opóźnienia i terminie, w którym informacja zostanie
udostępniona. Termin ten nie może być dłuższy niż 2 miesiące od dnia złożenia
wniosku.

Art. 14. 1. Udostępnianie informacji publicznej na wniosek następuje w sposób
i w formie zgodnych z wnioskiem, chyba że środki techniczne, którymi dysponuje
podmiot, nie umożliwiają udostępnienia w tej formie.

Art. 16. 1. Odmowa udostępnienia informacji publicznej oraz umorzenie postępowania
o udostępnienie informacji publicznej następuje w drodze decyzji.
2. Do decyzji stosuje się przepisy Kodeksu postępowania administracyjnego.

Art. 17. 1. Do postępowania o udostępnienie informacji publicznej stosuje się
przepisy Kodeksu postępowania administracyjnego, z wyłączeniem przepisów
o milczącym załatwieniu sprawy.

Art. 20. 1. Kto, wbrew ciążącemu na nim obowiązkowi, nie udostępnia informacji
publicznej, podlega grzywnie, karze ograniczenia wolności albo pozbawienia
wolności do roku.
"""

KPA_TEXT = """\
KODEKS POSTĘPOWANIA ADMINISTRACYJNEGO
(wyciąg przygotowany na potrzeby prototypu — nie stanowi tekstu jednolitego)

Art. 6. Organy administracji publicznej działają na podstawie przepisów prawa.

Art. 7. W toku postępowania organy administracji publicznej stoją na straży
praworządności i podejmują wszelkie kroki niezbędne do dokładnego wyjaśnienia
stanu faktycznego oraz do załatwienia sprawy, mając na względzie interes
społeczny i słuszny interes obywateli.

Art. 9. Organy administracji publicznej są obowiązane do należytego i wyczerpującego
informowania stron o okolicznościach faktycznych i prawnych, które mogą mieć wpływ
na ustalenie ich praw i obowiązków.

Art. 11. 1. Organy administracji publicznej powinny wyjaśniać stronom zasadność
przesłanek, którymi kierują się przy załatwieniu sprawy, aby w miarę możliwości
doprowadzić do wykonania przez strony decyzji bez potrzeby stosowania środków
przymusu.

Art. 35. 1. Organ administracji publicznej obowiązany jest załatwić sprawę bez
zbędnej zwłoki.
3. Załatwienie sprawy wymagającej postępowania wyjaśniającego powinno nastąpić
nie później niż w ciągu miesiąca, a sprawy szczególnie skomplikowanej — nie
później niż w ciągu dwóch miesięcy od dnia wszczęcia postępowania.
5. Do terminów nie wlicza się terminów przewidzianych w przepisach prawa
podatkowego dla dokonania określonych czynności, okresów zawieszenia
postępowania oraz okresów opóźnień spowodowanych z winy strony.

Art. 36. 1. Jeżeli sprawa nie została załatwiona w terminie, organ administracji
publicznej zawiadamia stronę o przyczynach opóźnienia i wskazuje nowy termin
załatwienia sprawy.

Art. 64. 1. Jeżeli podanie nie spełnia wymagań, organ administracji publicznej
wzywa do jego uzupełnienia w terminie 7 dni.

Art. 73. 1. Strona ma prawo wglądu w akta sprawy, sporządzania z nich notatek,
kopii lub odpisów.

Art. 77. 1. Organ administracji publicznej jest obowiązany zebrać i w sposób
wyczerpujący rozpatrzyć cały materiał dowodowy.

Art. 107. 1. Decyzja zawiera: oznaczenie organu, datę wydania, oznaczenie strony,
powołanie podstawy prawnej, rozstrzygnięcie, uzasadnienie faktyczne i prawne,
pouczenie o środkach odwoławczych, podpis z podaniem imienia, nazwiska
i stanowiska służbowego.

Art. 109. 1. Organ administracji publicznej, który wydał decyzję, może ją zmienić
lub uchylić, jeżeli wymaga tego interes społeczny lub słuszny interes strony.
"""

ZARZADZENIE_TEXT = """\
ZARZĄDZENIE NR 536/2024
PREZYDENTA MIASTA BYDGOSZCZY
z dnia 23 września 2024 r.
w sprawie zasad i trybu udostępniania informacji publicznej

Na podstawie art. 33 ust. 1 i 3 ustawy z dnia 8 marca 1990 r. o samorządzie gminnym
(Dz. U. z 2024 r. poz. 609, 721), art. 4 ust. 1 pkt 4, art. 9 ust. 2 ustawy z dnia
6 września 2001 r. o dostępie do informacji publicznej (Dz. U. z 2022 r. poz. 902)
i § 15 ust. 1 rozporządzenia Ministra Spraw Wewnętrznych i Administracji z dnia
18 stycznia 2007 r. w sprawie Biuletynu Informacji Publicznej (Dz. U. z 2007 r.
Nr 10, poz. 68) zarządza się, co następuje.

Rozdział I
Przepisy ogólne

§ 1. Ilekroć w Zarządzeniu jest mowa o:
1) BIP — należy przez to rozumieć Biuletyn Informacji Publicznej Urzędu Miasta
   Bydgoszczy www.bip.um.bydgoszcz.pl;
2) Urzędzie — należy przez to rozumieć Urząd Miasta Bydgoszczy;
3) Wydziałach — należy przez to rozumieć komórki organizacyjne Urzędu o tej nazwie
   oraz inne wewnętrzne komórki organizacyjne, wchodzące w skład Urzędu na prawach
   Wydziału;
4) Dyrektorze — należy przez to rozumieć Dyrektora Wydziału Urzędu lub kierującego
   pracą komórki organizacyjnej wchodzącej w skład Urzędu na prawach Wydziału;
5) Administratorze serwera BIP — należy przez to rozumieć dostawcę technologii
   serwisu BIP;
6) AIP — należy przez to rozumieć Administratora Informacji Publicznej, tj. osobę
   upoważnioną w Urzędzie do udzielania odpowiedzi w sprawie udzielenia informacji
   publicznej lub decyzji administracyjnych w tym zakresie;
7) udip — należy przez to rozumieć ustawę z dnia 6 września 2001 r. o dostępie do
   informacji publicznej;
8) udcsi — należy przez to rozumieć ustawę z dnia 4 kwietnia 2019 r. o dostępności
   cyfrowej stron internetowych i aplikacji mobilnych podmiotów publicznych.

Rozdział II
Biuletyn Informacji Publicznej Urzędu Miasta Bydgoszczy — Redakcja BIP

§ 2. 1. Redakcję BIP tworzą:
1) Zespół Redakcyjny BIP;
2) Zespół Redaktorów Wydziałowych.
2. Pracami Redakcji BIP kieruje Redaktor Główny BIP.

§ 3. 1. Powołuje się Zespół Redakcyjny BIP w składzie:
1) Redaktor Główny BIP — pracownik Biura Komunikacji Społecznej Urzędu Miasta
   Bydgoszczy;
2) Redaktorzy Wydziałowi.
2. Do zadań Zespołu Redakcyjnego BIP należy:
1) sprawowanie nadzoru nad aktualizowaniem informacji umieszczanych w BIP;
2) dostosowywanie BIP do obowiązujących przepisów prawa;
3) organizowanie spotkań w celu ujednolicenia polityki informacyjnej Urzędu;
4) w razie potrzeby, zapraszanie na spotkania osób niebędących członkami Zespołu
   Redakcyjnego BIP.
3. Pracami Zespołu Redakcyjnego BIP kieruje Redaktor Główny BIP, który w zależności
   od potrzeb przydziela zadania poszczególnym Redaktorom Wydziałowym.

§ 4. 1. Powołuje się Zespół Redaktorów Wydziałowych.
2. W jego skład wchodzą pracownicy wyznaczeni przez Dyrektorów Wydziałów Urzędu.
3. Do zadań Redaktorów Wydziałowych należy:
1) dostosowywanie informacji z Wydziałów do wymagań redakcyjnych określonych przez
   Zespół Redakcyjny BIP;
2) opracowywanie i publikacja informacji zgodnie z wymogami udip, udcsi i Polityki
   Bezpieczeństwa Informacji Urzędu Miasta Bydgoszczy;
3) uczestniczenie w spotkaniach organizowanych przez Zespół Redakcyjny BIP, celem
   ujednolicenia polityki informacyjnej Urzędu;
4) monitorowanie treści zawartych w BIP, zgłaszanie uwag oraz propozycji zmian
   Redaktorowi Głównemu BIP.

§ 5. 1. Informacja podlegająca publikacji powinna spełniać wymogi udip, udcsi
i Polityki Bezpieczeństwa Informacji Urzędu Miasta Bydgoszczy.
2. W szczególnych przypadkach niemożności opublikowania informacji przez Redaktora
Wydziałowego, zostaje ona przesłana na adres bip@um.bydgoszcz.pl w celu
opublikowania jej przez Redaktora Głównego BIP.
3. Odpowiedzialność za treść przekazywanych i publikowanych informacji ponoszą
Redaktorzy Wydziałowi.
4. Informację przekazaną do publikacji zatwierdza Dyrektor danego Wydziału.
5. Nadzór nad Redaktorem Wydziałowym sprawuje Dyrektor Wydziału.
6. Nadzór nad zamieszczaniem i publikowaniem w BIP aktów podpisanych przez
Przewodniczącego Rady Miasta sprawuje Dyrektor Biura Rady Miasta.

§ 6. Redaktor Główny BIP jest odpowiedzialny za:
1) publikowanie informacji przekazywanych przez podmioty zewnętrzne;
2) publikowanie informacji w przypadku niemożności po stronie Redaktora
   Wydziałowego;
3) przekazywanie ministrowi właściwemu do spraw informatyzacji informacji
   niezbędnych do prowadzenia strony głównej BIP, w tym o adresie URL BIP oraz
   powiadomienie ministra o zmianach w treści tych informacji;
4) współpracę z Administratorem serwera BIP w zakresie zabezpieczenia treści
   informacji umieszczonych w BIP;
5) sprawowanie ogólnego nadzoru nad funkcjonowaniem BIP.

Rozdział III
Udostępnianie informacji publicznej na wniosek

§ 7. Udostępnianie informacji publicznej na wniosek odbywa się na zasadach
określonych w udip oraz zgodnie z przyjętą Polityką Bezpieczeństwa Informacji
Urzędu Miasta Bydgoszczy.

§ 8. 1. Informacja publiczna, która nie została opublikowana w BIP, jest
udostępniana na wniosek. Jeżeli wnioskowana informacja została opublikowana w BIP,
wnioskodawcy wskazuje się dokładny adres strony BIP zawierającej informację
publiczną.
2. Informacja publiczna niepublikowana w BIP, która może być udostępniona
niezwłocznie, może być udostępniona bez pisemnego wniosku.

§ 9. 1. AIP koordynuje rozpoznawanie wniosków i przygotowuje odpowiedzi na wnioski
na podstawie dokumentacji przekazanej przez Wydziały.
2. Wpływające do Urzędu wnioski przekazywane są AIP i są przez niego rejestrowane.
3. W przypadku gdy wniosek złożony zostanie bezpośrednio w Wydziale, powinien być
niezwłocznie przekazany (w tym w formie elektronicznej) AIP.

§ 10. AIP przekazuje niezwłocznie właściwym merytorycznie Wydziałom zakres
informacji określonych we wniosku o udostępnienie informacji w celu ich
rozpatrzenia.

§ 11. 1. Wydziały przygotowują projekt odpowiedzi na wniosek w części odpowiadającej
ich zakresowi działania, udzielają wyjaśnień, a także przygotowują dokumentację
niezbędną do rozpatrzenia wniosku. Projekt odpowiedzi powinien być przesłany na
adres bip@um.bydgoszcz.pl w terminie określonym przez AIP.
2. Udostępnianie informacji publicznej na wniosek następuje w sposób i w formie
zgodnych z wnioskiem, chyba że środki techniczne, którymi dysponuje Urząd, nie
umożliwiają udostępnienia informacji w sposób i w formie określonych we wniosku.
Jeżeli informacja nie może być udostępniona w sposób lub w formie określonych we
wniosku, Wydział niezwłocznie powiadamia pisemnie AIP o przyczynach braku
możliwości udostępnienia informacji zgodnie z wnioskiem i wskazuje, w jaki sposób
lub w jakiej formie informacja może być udostępniona.
3. Jeżeli po otrzymaniu wniosku Wydział stwierdza, że nie jest w posiadaniu
wnioskowanej informacji, niezwłocznie informuje o tym AIP i wskazuje, o ile jest
znana, jednostkę właściwą w zakresie wnioskowanych informacji.
4. Jeżeli do przygotowania odpowiedzi na wniosek niezbędna jest dokumentacja
przechowywana w archiwum zakładowym Urzędu, właściwym do przygotowania projektu
odpowiedzi jest Wydział, który przekazał sprawę do archiwum zakładowego Urzędu lub
jego następca. Jeżeli wniosek dotyczy Wydziału, który został zlikwidowany, a inny
Wydział nie przejął jego zadań, właściwym do przygotowania projektu odpowiedzi jest
Wydział prowadzący archiwum zakładowe.
5. W przypadku gdy projekt odpowiedzi nie może być przesłany w określonym przez AIP
terminie, Wydział powiadamia pisemnie AIP o powodach opóźnienia oraz o terminie,
w jakim projekt odpowiedzi zostanie przekazany.
6. W przypadku gdy informacja ma zostać udostępniona poprzez wgląd w akta,
dokumentację przygotowuje oraz udostępnia w swojej siedzibie Wydział będący
w dyspozycji wnioskowanych materiałów, po czym bez zbędnej zwłoki przesyła do AIP
potwierdzenie wglądu do dokumentacji.
7. W przypadku gdy Wydział uzna wnioskowaną informację za informację przetworzoną,
przesyła do AIP projekt odpowiedzi zawierający uzasadnienie dla uznania
wnioskowanej informacji za informację przetworzoną.
8. Informacja przekazywana jest po dokonaniu przez Wydział właściwy do przygotowania
projektu odpowiedzi koniecznej anonimizacji.
9. W przypadku gdy wniosek obejmuje udzielenie informacji publicznej chronionej
prawem, Wydział przygotowuje projekt decyzji administracyjnej o odmowie
udostępnienia informacji publicznej.

§ 12. 1. Decyzje w sprawach związanych z udostępnianiem informacji publicznej wydaje
Prezydent lub upoważnieni Zastępcy Prezydenta Miasta, Sekretarz, Skarbnik oraz
pracownik Biura Komunikacji Społecznej Urzędu Miasta Bydgoszczy.
2. Kopie odpowiedzi, decyzji, odwołań, skarg i rozstrzygnięć w sprawach
udostępnienia informacji publicznej podlegają przekazaniu AIP.

Rozdział IV
Przepisy końcowe

§ 13. Wykonanie zarządzenia powierza się Dyrektorom Wydziałów Urzędu Miasta
Bydgoszczy.

§ 14. Traci moc Zarządzenie Prezydenta Miasta Bydgoszczy Nr 151/2011 z dnia
25 lutego 2011 roku w sprawie zasad i trybu udostępniania informacji publicznej,
zmienione Zarządzeniem Prezydenta Miasta Bydgoszczy Nr 681/2012 z dnia
5 października 2012 roku.

§ 15. Zarządzenie wchodzi w życie z dniem podpisania.
"""


# ──────────────────────────── anonimizacja ─────────────────────────────
# Teksty z markerami {{kategoria:wartość}} — offsety liczone programowo.
ANON_SAMPLES = [
    (
        "a01",
        "Wnioskodawca {{imie_nazwisko:Jan Kowalski}}, PESEL {{pesel:85041212345}}, "
        "zamieszkały przy {{adres:ul. Gdańska 42/7, 85-005 Bydgoszcz}}, zwraca się "
        "o udostępnienie informacji o wydatkach na promocję.",
    ),
    (
        "a02",
        "Kontakt z wnioskodawcą: {{telefon:+48 601 234 567}}, e-mail "
        "{{email:jan.kowalski@example.com}}. Sprawę prowadzi {{imie_nazwisko:Anna Nowak}}.",
    ),
    (
        "a03",
        "Spółka {{imie_nazwisko:Przedsiębiorstwo Budowlane Sp. z o.o.}} o NIP "
        "{{nip:7791234567}} i REGON {{regon:123456789}} złożyła ofertę w postępowaniu "
        "przetargowym nr ZP.271.42.2026.",
    ),
    (
        "a04",
        "W dniu 14 marca 2026 r. {{imie_nazwisko:Piotr Wiśniewski}} okazał dowód osobisty "
        "serii {{dowod:ABC 123456}} i złożył wniosek w imieniu własnym.",
    ),
    (
        "a05",
        "Wynagrodzenie brutto pracownika wyniosło 8 420,00 zł. Numer konta do wypłaty: "
        "{{iban:PL61 1090 1014 0000 0712 1981 2874}}. Data urodzenia: "
        "{{data_urodzenia:12.04.1985}}.",
    ),
    (
        "a06",
        "Paszport {{paszport:AB1234567}} został przedłożony do wglądu przez "
        "{{imie_nazwisko:Marię Zielińską}} w dniu 2 lutego 2026 r.",
    ),
    (
        "a07",
        "Zgłoszenie przyjął {{imie_nazwisko:starszy inspektor Tomasz Lewandowski}}, "
        "tel. {{telefon:52 585 88 88}}, e-mail {{email:t.lewandowski@um.bydgoszcz.pl}}.",
    ),
    (
        "a08",
        "Wniosek dotyczy nieruchomości położonej przy {{adres:ul. Dworcowa 12, "
        "85-009 Bydgoszcz}}, oznaczonej jako działka nr 142/3, obręb 0042.",
    ),
    (
        "a09",
        "Składający wniosek {{imie_nazwisko:Krzysztof Dąbrowski}}, PESEL "
        "{{pesel:72061598765}}, NIP {{nip:5541234567}}, prosi o udostępnienie "
        "protokołów kontroli.",
    ),
    (
        "a10",
        "Odpowiedź została podpisana przez {{imie_nazwisko:Dyrektora Wydziału "
        "Gospodarki Komunalnej Michała Sikorskiego}} w dniu 3 marca 2026 r.",
    ),
    (
        "a11",
        "Dane kontaktowe: {{email:kontakt@firma-przyklad.pl}}, {{telefon:22 123 45 67}}, "
        "adres siedziby {{adres:ul. Prosta 51, 00-838 Warszawa}}.",
    ),
    (
        "a12",
        "Pracownik {{imie_nazwisko:Aleksandra Kaczmarek}} zatrudniona od 1 września 2019 r., "
        "PESEL {{pesel:91020312345}}, nr konta {{iban:PL27 1140 2004 0000 3802 3456 7890}}.",
    ),
    (
        "a13",
        'Wniosek złożył {{imie_nazwisko:Robert Mazur}} w imieniu stowarzyszenia '
        '"Zielona Bydgoszcz", REGON {{regon:340123456}}, e-mail '
        "{{email:biuro@zielonabydgoszcz.pl}}.",
    ),
    (
        "a14",
        "Sprawa nr BKS.IV.1431.42.2026 dotyczy {{imie_nazwisko:Grażyny Pawlak}}, "
        "zamieszkałej przy {{adres:ul. Nakielska 108/4, 85-391 Bydgoszcz}}.",
    ),
    (
        "a15",
        "Numer PESEL {{pesel:00251234567}} należy do osoby niepełnoletniej, dlatego "
        "dane {{imie_nazwisko:Zofii Adamczyk}} podlegają szczególnej ochronie.",
    ),
    (
        "a16",
        "Korespondencję należy kierować na adres {{adres:skrytka pocztowa 142, "
        "85-001 Bydgoszcz}} lub telefonicznie {{telefon:512 345 678}}.",
    ),
    (
        "a17",
        "Dowód osobisty {{dowod:XYZ 987654}} wydany przez Prezydenta Miasta "
        "Bydgoszczy został zwrócony {{imie_nazwisko:Łukaszowi Grabowskiemu}}.",
    ),
    (
        "a18",
        "Faktura nr FV/2026/03/142 została wystawiona dla {{imie_nazwisko:Transport "
        "Miejski Sp. z o.o.}}, NIP {{nip:9531234567}}, REGON {{regon:091234567}}.",
    ),
    (
        "a19",
        "Wnioskodawczyni {{imie_nazwisko:Barbara Wójcik}}, ur. {{data_urodzenia:"
        "07.11.1968}}, PESEL {{pesel:68110712345}}, prosi o wgląd w akta sprawy.",
    ),
    (
        "a20",
        "Osobą odpowiedzialną za realizację jest {{imie_nazwisko:inż. Rafał Król}}, "
        "tel. {{telefon:52 585 80 00}}, e-mail {{email:r.krol@zdmikp.bydgoszcz.pl}}.",
    ),
]

MARKER_RE = re.compile(r"\{\{(\w+):(.*?)\}\}", re.DOTALL)


def strip_markers(text: str) -> tuple[str, list[dict]]:
    """Zamienia {{kategoria:wartość}} na wartość i zwraca offsety."""
    spans: list[dict] = []
    out: list[str] = []
    pos = 0
    cursor = 0
    for m in MARKER_RE.finditer(text):
        out.append(text[pos : m.start()])
        cursor += m.start() - pos
        value = m.group(2)
        spans.append(
            {
                "start": cursor,
                "end": cursor + len(value),
                "text": value,
                "category": m.group(1),
            }
        )
        out.append(value)
        cursor += len(value)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), spans


def build_anonymization() -> list[dict]:
    rows = []
    for sid, marked in ANON_SAMPLES:
        text, spans = strip_markers(marked)
        rows.append({"id": sid, "text": text, "spans": spans})
    return rows


# ────────────────────────────── dokumenty ──────────────────────────────
WNIOSEK_1 = """\
Bydgoszcz, 20 lutego 2026 r.

Jan Kowalski
ul. Gdańska 42/7
85-005 Bydgoszcz

Urząd Miasta Bydgoszczy
Biuro Komunikacji Społecznej
ul. Jezuicka 1
85-102 Bydgoszcz

WNIOSEK O UDOSTĘPNIENIE INFORMACJI PUBLICZNEJ

Na podstawie art. 2 ust. 1 ustawy z dnia 6 września 2001 r. o dostępie do
informacji publicznej wnoszę o udostępnienie informacji publicznej w zakresie:

1. Wysokości wynagrodzeń pracowników Urzędu Miasta Bydgoszczy zatrudnionych
   na stanowiskach kierowniczych w 2025 roku.
2. Wysokości nagród i premii przyznanych tym osobom w 2025 roku.

Wnoszę o udostępnienie informacji w formie elektronicznej, na adres e-mail:
jan.kowalski@example.com.

Informacje proszę przekazać w formie zestawienia tabelarycznego z podziałem
na wydziały i biura.

Z poważaniem
Jan Kowalski
"""

WNIOSEK_2 = """\
Bydgoszcz, 2 marca 2026 r.

Redakcja „Głos Bydgoszczy"
ul. Długa 18
85-034 Bydgoszcz

Urząd Miasta Bydgoszczy
ul. Jezuicka 1
85-102 Bydgoszcz

WNIOSEK O UDOSTĘPNIENIE INFORMACJI PUBLICZNEJ

Działając jako redakcja w rozumieniu art. 7 ust. 2 pkt 5 ustawy o dostępie do
informacji publicznej, wnoszę o udostępnienie:

1. Kopii umów najmu lokali komunalnych położonych przy ul. Dworcowej
   w Bydgoszczy, zawartych w latach 2024-2025.
2. Wykazu stawek czynszu obowiązujących dla tych lokali.

Wnoszę o udostępnienie w formie elektronicznej (skany PDF).

Z poważaniem
Anna Nowak
Redaktor naczelna
"""

WNIOSEK_3 = """\
Bydgoszcz, 11 marca 2026 r.

Stowarzyszenie „Zielona Bydgoszcz"
ul. Prosta 51
85-001 Bydgoszcz
NIP 5541234567
REGON 340123456

Urząd Miasta Bydgoszczy
Wydział Ochrony Środowiska
ul. Jezuicka 1
85-102 Bydgoszcz

WNIOSEK O UDOSTĘPNIENIE INFORMACJI PUBLICZNEJ

Wnoszę o udostępnienie informacji publicznej w zakresie:

1. Liczby zezwoleń na usunięcie drzew wydanych w 2025 roku.
2. Liczby nasadzeń zastępczych wykonanych w 2025 roku.
3. Wpływów z opłat za usunięcie drzew w 2025 roku.

Informacje proszę przekazać w formie elektronicznej.

Z poważaniem
Robert Mazur
Prezes Zarządu
"""

ODPOWIEDZ_WYDZIAL = """\
Urząd Miasta Bydgoszczy
Wydział Organizacji i Kadr
ul. Jezuicka 1, 85-102 Bydgoszcz

Bydgoszcz, 10 marca 2026 r.

Znak: WOK.1435.1.2026

Do: Biuro Komunikacji Społecznej

W odpowiedzi na zapytanie z dnia 24 lutego 2026 r. dotyczące wniosku
BKS.IV.1431.1.2026 uprzejmie informuję:

1. Przeciętne miesięczne wynagrodzenie brutto na stanowiskach kierowniczych
   w Urzędzie Miasta Bydgoszczy w 2025 roku wyniosło 14 218,40 zł.

2. Zestawienie wynagrodzeń w podziale na wydziały i biura przedstawia się
   następująco:
   - Wydział Architektury i Urbanistyki: 13 842,00 zł
   - Wydział Budżetu i Księgowości: 14 102,50 zł
   - Wydział Edukacji: 13 218,00 zł
   - Wydział Gospodarki Nieruchomościami: 13 640,00 zł
   - Wydział Inwestycji: 14 842,00 zł
   - Wydział Organizacji i Kadr: 13 918,00 zł
   - Wydział Promocji Miasta: 13 412,00 zł
   - Biuro Rady Miasta: 13 284,00 zł
   - Biuro Prawne: 15 218,00 zł

3. Łączna kwota nagród i premii przyznanych w 2025 roku osobom na stanowiskach
   kierowniczych wyniosła 486 200 zł.

4. Dane osobowe poszczególnych pracowników podlegają ochronie na podstawie
   art. 5 ust. 2 ustawy o dostępie do informacji publicznej i nie podlegają
   udostępnieniu.

Kierownik Wydziału
Organizacji i Kadr
/-/ Monika Wiśniewska
"""

ODPOWIEDZ_WYDZIAL_2 = """\
Urząd Miasta Bydgoszczy
Wydział Gospodarki Nieruchomościami
ul. Jezuicka 1, 85-102 Bydgoszcz

Bydgoszcz, 12 marca 2026 r.

Znak: WGN.1435.2.2026

Do: Biuro Komunikacji Społecznej

W odpowiedzi na zapytanie z dnia 4 marca 2026 r. w sprawie wniosku
BKS.IV.1431.2.2026 informuję, że przygotowanie odpowiedzi wymaga kwerendy
w aktach lokalowych.

Gmina Bydgoszcz posiada 2 843 lokale komunalne. W rejonie ul. Dworcowej
znajduje się 68 lokali komunalnych. W latach 2024-2025 zawarto 14 umów najmu
dotyczących tych lokali.

Średnia stawka czynszu dla lokali przy ul. Dworcowej wynosi 12,84 zł/m².
Stawki mieszczą się w przedziale od 9,20 zł/m² do 16,40 zł/m² w zależności
od standardu lokalu.

Kopie umów zawierają dane osobowe najemców (imiona, nazwiska, numery PESEL,
adresy) i wymagają anonimizacji przed udostępnieniem.

Kierownik Wydziału
Gospodarki Nieruchomościami
/-/ Andrzej Lewandowski
"""


def write_pdf(path: Path, title: str, body: str) -> None:
    from fpdf import FPDF

    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.add_font("DejaVu", "", "/usr/share/fonts/TTF/DejaVuSans.ttf")
    pdf.set_font("DejaVu", size=10)
    pdf.multi_cell(0, 5.5, body)
    pdf.output(str(path))


def write_docx(path: Path, title: str, body: str) -> None:
    from docx import Document

    doc = Document()
    doc.add_heading(title, level=1)
    for para in body.split("\n\n"):
        doc.add_paragraph(para.strip())
    doc.save(str(path))


def build_documents() -> list[str]:
    docs = ROOT / "documents"
    docs.mkdir(parents=True, exist_ok=True)
    made = []

    write_pdf(docs / "wniosek-01-wynagrodzenia.pdf", "Wniosek UDIP", WNIOSEK_1)
    made.append("wniosek-01-wynagrodzenia.pdf")

    write_pdf(docs / "wniosek-02-najem-lokali.pdf", "Wniosek UDIP", WNIOSEK_2)
    made.append("wniosek-02-najem-lokali.pdf")

    write_docx(docs / "wniosek-03-wycinka-drzew.docx", "Wniosek UDIP", WNIOSEK_3)
    made.append("wniosek-03-wycinka-drzew.docx")

    write_pdf(
        docs / "odpowiedz-wydzialu-01.pdf", "Odpowiedź wydziału", ODPOWIEDZ_WYDZIAL
    )
    made.append("odpowiedz-wydzialu-01.pdf")

    write_docx(
        docs / "odpowiedz-wydzialu-02.docx", "Odpowiedź wydziału", ODPOWIEDZ_WYDZIAL_2
    )
    made.append("odpowiedz-wydzialu-02.docx")

    return made


# ──────────────────────────────── main ─────────────────────────────────
def main() -> None:
    (ROOT / "cases").mkdir(exist_ok=True)
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "statutes").mkdir(exist_ok=True)
    (ROOT / "anonymization").mkdir(exist_ok=True)

    (ROOT / "cases" / "cases.json").write_text(
        json.dumps(CASES, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "archive" / "archive.json").write_text(
        json.dumps(build_archive(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "departments.json").write_text(
        json.dumps(build_departments(), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    (ROOT / "statutes" / "udip.txt").write_text(UDIP_TEXT, encoding="utf-8")
    (ROOT / "statutes" / "kpa.txt").write_text(KPA_TEXT, encoding="utf-8")
    (ROOT / "statutes" / "zarzadzenie-536-2024.txt").write_text(
        ZARZADZENIE_TEXT, encoding="utf-8"
    )

    anon = build_anonymization()
    (ROOT / "anonymization" / "labeled.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in anon) + "\n",
        encoding="utf-8",
    )

    docs = build_documents()

    print(f"cases:        {len(CASES)}")
    print(f"archive:      {len(build_archive())}")
    print(f"departments:  {len(build_departments())}")
    print(f"statutes:     3")
    print(f"anonymization:{len(anon)}")
    print(f"documents:    {len(docs)} -> {', '.join(docs)}")


if __name__ == "__main__":
    main()
