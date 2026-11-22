#!/usr/bin/env python3
"""Buduje prezentację konkursową (10 slajdów) jako jeden plik HTML i PDF.

Źródła obrazów: zrzuty ekranu z ``video/src/assets/shots`` przycięte do
``prezentacja/assets``. Fonty: Inter z ``video/src/assets/fonts``.

Uruchomienie::

    python3 prezentacja/build.py

Wynik: ``prezentacja/prezentacja.html`` i ``prezentacja/prezentacja.pdf``.
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "prezentacja"
ASSETS = HERE / "assets"
FONTS = ROOT / "video" / "src" / "assets" / "fonts"

CHROME = Path(
    "/home/trollyou/.t3/tools/chrome-headless-shell/linux64/157.0.8103.38/chrome-headless-shell"
)

# ---------------------------------------------------------------- kolory

BG = "#060A13"
PANEL = "#0C1524"
BORDER = "#1E2C42"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
DIM = "#64748B"
BLUE = "#3B82F6"
SKY = "#38BDF8"
AMBER = "#F59E0B"
GREEN = "#10B981"
VIOLET = "#8B5CF6"
RED = "#EF4444"

TEAM = ["sLaRpNaTiOn"]
TOTAL = 10


# ---------------------------------------------------------------- pomocnicze


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def font_css() -> str:
    """Inter 400/500/600/700/800, łacina + łacina rozszerzona (polskie znaki)."""
    out: list[str] = []
    for weight in (400, 500, 600, 700, 800):
        for subset in ("latin", "latin-ext"):
            path = FONTS / f"inter-{weight}-{subset}.woff2"
            if not path.exists():
                continue
            out.append(
                "@font-face{font-family:'Inter';font-style:normal;"
                f"font-weight:{weight};font-display:block;"
                f"src:url(data:font/woff2;base64,{b64(path)}) format('woff2');}}"
            )
    return "\n".join(out)


def img(name: str) -> str:
    return f"data:image/png;base64,{b64(ASSETS / name)}"


def shot(name: str, width: int, *, radius: int = 14) -> str:
    """Zrzut ekranu w ramce: jasny interfejs na ciemnym tle."""
    return (
        f'<div class="shot" style="width:{width}px;border-radius:{radius}px">'
        f'<img src="{img(name)}" alt=""></div>'
    )


def kicker(text: str, color: str = BLUE) -> str:
    return (
        f'<div class="kicker" style="color:{color}">'
        f'<span class="kicker-line" style="background:{color}"></span>{text}</div>'
    )


def head(text: str, size: int = 54) -> str:
    return f'<h1 class="head" style="font-size:{size}px">{text}</h1>'


def footer(n: int) -> str:
    return (
        '<div class="foot">'
        '<span>Capricorn · HackNation 2026 · Miasto Bydgoszcz</span>'
        f'<span>{n:02d} / {TOTAL:02d}</span>'
        "</div>"
    )


def slide(n: int, body: str, *, cls: str = "") -> str:
    return f'<section class="slide {cls}"><div class="pad">{body}</div>{footer(n)}</section>'


def bullets(items: list[str], color: str = BLUE, size: int = 21) -> str:
    rows = "".join(
        f'<li><span class="dot" style="background:{color}"></span><span>{t}</span></li>'
        for t in items
    )
    return f'<ul class="bullets" style="font-size:{size}px">{rows}</ul>'


def stat(value: str, label: str, color: str) -> str:
    return (
        f'<div class="stat"><div class="stat-value" style="color:{color}">{value}</div>'
        f'<div class="stat-label">{label}</div></div>'
    )


def metrics(items: list[tuple[str, str, str]]) -> str:
    """Pasek metryk: duża wartość i etykieta pod nią."""
    cells = "".join(
        f'<div class="metric"><div class="metric-value" style="color:{c}">{v}</div>'
        f'<div class="metric-label">{label}</div></div>'
        for v, label, c in items
    )
    return f'<div class="metrics">{cells}</div>'


def cards3(items: list[tuple[str, str, str]]) -> str:
    """Trzy karty w jednym rzędzie: tytuł w kolorze, opis pod nim."""
    cells = "".join(
        f'<div class="card3"><div class="card3-title" style="color:{c}">{t}</div>'
        f'<div class="card3-text">{d}</div></div>'
        for t, d, c in items
    )
    return f'<div class="cards3">{cells}</div>'


# ---------------------------------------------------------------- slajdy


def s01() -> str:
    team = " · ".join(TEAM)
    body = f"""
<div class="title-grid">
  <div class="title-left">
    {kicker("HACKNATION 2026 · MIASTO BYDGOSZCZ", SKY)}
    <h1 class="title">Capricorn</h1>
    <p class="title-sub">Inteligentny asystent urzędnika: generator odpowiedzi
    na wnioski o udostępnienie informacji publicznej, z kalendarzem terminów</p>
    <div class="title-team">
      <div class="title-team-label">ZESPÓŁ</div>
      <div class="title-team-names">{team}</div>
    </div>
    <div class="chips">
      <span class="chip chip-blue">Działający prototyp</span>
      <span class="chip">8 modułów</span>
      <span class="chip">Tryb offline</span>
      <span class="chip">564 testy backendu · 199 frontendu</span>
    </div>
  </div>
  <div class="title-right">
    {shot("pulpit.png", 880, radius=18)}
    <div class="title-caption">Pulpit: co jest po terminie, co ma termin dziś,
    co zamyka się w najbliższych dniach.</div>
  </div>
</div>
"""
    return slide(1, body, cls="s-title")


def s02() -> str:
    pains = [
        (
            "Archiwum bez wyszukiwarki",
            "Podobne sprawy z 2024 i 2025 roku leżą w folderach. Nikt nie ma czasu ich czytać, więc pismo powstaje od zera.",
            SKY,
        ),
        (
            "Dane osobowe w każdej odpowiedzi",
            "PESEL, adres, telefon i e-mail wnioskodawcy trzeba wyciąć przed publikacją w BIP, ręcznie, pod presją terminu.",
            GREEN,
        ),
        (
            "Terminy pilnowane w arkuszu",
            "Jeden plik, jedna osoba, brak historii zmian. Nikt nie odtworzy, kto i kiedy przesunął sprawę.",
            AMBER,
        ),
    ]
    pain_html = "".join(
        f'<div class="pain"><span class="pain-bar" style="background:{c}"></span>'
        f'<div><div class="pain-title">{t}</div><div class="pain-text">{d}</div></div></div>'
        for t, d, c in pains
    )
    body = f"""
{kicker("PROBLEM", RED)}
{head("Czternaście dni na odpowiedź.<br>Setki godzin na przepisywanie.")}
<div class="two-col" style="margin-top:34px">
  <div class="col" style="width:820px">
    <p class="lead">Wniosek o informację publiczną ma ustawowy termin 14 dni
    (art. 13 ust. 2 UDIP). W tym czasie urzędnik musi przeszukać archiwum, ustalić,
    które komórki odpowiadają, zebrać materiały, napisać pismo i usunąć z niego
    dane osobowe.</p>
    <div class="stats">
      {stat("14 dni", "ustawowy termin odpowiedzi, liczony od wpływu wniosku", RED)}
      {stat("49", "spraw w archiwum demonstracyjnym: tyle przeszukuje się ręcznie", SKY)}
      {stat("26", "komórek organizacyjnych UMB, z których trzeba pozyskać materiały", VIOLET)}
    </div>
  </div>
  <div class="col" style="width:820px">{pain_html}</div>
</div>
<div class="ba">
  <div class="ba-col ba-before">
    <div class="ba-label" style="color:{RED}">DZIŚ</div>
    <div class="ba-text">Arkusz, foldery i pamięć jednej osoby. Pismo powstaje od zera,
    a dane osobowe wycina się ręcznie, pod presją terminu.</div>
  </div>
  <div class="ba-arrow">→</div>
  <div class="ba-col ba-after">
    <div class="ba-label" style="color:{GREEN}">Z ASYSTENTEM</div>
    <div class="ba-text">Jedna ścieżka: wniosek, archiwum, wydziały, projekt z cytatami,
    anonimizacja do akceptacji. Urzędnik czyta i decyduje.</div>
  </div>
</div>
<div class="callout" style="margin-top:auto">
  <span class="callout-mark" style="background:{BLUE}"></span>
  Cel: z kilku dni do kilku minut, bez oddawania decyzji maszynie.
</div>
"""
    return slide(2, body)


def s03() -> str:
    steps = [
        ("Wniosek", "PDF albo DOCX", BLUE),
        ("Archiwum", "podobne sprawy", SKY),
        ("Wydziały", "kto odpowiada", VIOLET),
        ("Projekt", "pismo z cytatami", AMBER),
        ("Anonimizacja", "dane usunięte", GREEN),
        ("Wysyłka", "decyzja urzędnika", BLUE),
    ]
    boxes = []
    for i, (title, sub, color) in enumerate(steps):
        boxes.append(
            f'<div class="step"><span class="step-bar" style="background:{color}"></span>'
            f'<div class="step-num" style="color:{color}">0{i + 1}</div>'
            f'<div class="step-title">{title}</div>'
            f'<div class="step-sub">{sub}</div></div>'
        )
        if i < len(steps) - 1:
            boxes.append('<div class="step-arrow">→</div>')

    modules = [
        ("cases", "kalendarz"),
        ("ingest", "dokumenty"),
        ("archive", "archiwum"),
        ("routing", "wydziały"),
        ("drafting", "generator"),
        ("anonymize", "anonimizacja"),
        ("inference", "modele"),
        ("audit", "audyt"),
    ]
    mod_html = "".join(
        f'<span class="mod"><b>{n}</b>{d}</span>' for n, d in modules
    )

    body = f"""
{kicker("POMYSŁ", BLUE)}
{head("Jedna ścieżka: od wgranego wniosku do wysłanej odpowiedzi")}
<div class="steps">{"".join(boxes)}</div>
<div class="mods-block">
  <div class="mods-label">OSIEM MODUŁÓW, KAŻDY Z DWOMA ADAPTERAMI</div>
  <div class="mods">{mod_html}</div>
</div>
{cards3([
    ("Wszystko zostaje w urzędzie", "Dokumenty, fragmenty i wektory leżą w jednym pliku SQLite na dysku urzędu.", BLUE),
    ("Każdy krok ma właściciela", "Stan sprawy zmienia urzędnik. Narzędzie proponuje, nie wysyła.", SKY),
    ("Moduł da się podmienić", "Port i dwa adaptery: atrapa do demo, implementacja realna na produkcję.", VIOLET),
])}
{metrics([
    ("8", "modułów domenowych, każdy za własnym portem", BLUE),
    ("2", "adaptery na moduł: atrapa i implementacja realna", SKY),
    ("1", "plik SQLite z całą bazą urzędu", VIOLET),
    ("564", "testy backendu i 199 frontendu", GREEN),
])}
<div class="callout" style="margin-top:20px">
  <span class="callout-mark" style="background:{SKY}"></span>
  Port i dwa adaptery: deterministyczna atrapa oraz implementacja realna.
  Moduł przełącza się zmienną środowiskową, bez zmiany kodu; dlatego demo działa
  bez modelu i bez sieci, a ta sama ścieżka przechodzi test end-to-end na realnych.
</div>
"""
    return slide(3, body)


def s04() -> str:
    statuses = [
        ("a", "brak działań"),
        ("b", "zapytania wysłane"),
        ("c", "kwerenda"),
        ("d", "przygotowana odpowiedź"),
        ("e", "odpowiedź wysłana"),
    ]
    st_html = "".join(
        f'<span class="status"><b>{k}</b>{v}</span>' for k, v in statuses
    )
    body = f"""
{kicker("MODUŁ A · KALENDARZ WNIOSKÓW", BLUE)}
{head("Wszystkie terminy na jednym ekranie")}
<div class="two-col" style="margin-top:30px;align-items:flex-start">
  <div class="col" style="width:460px">
    {bullets([
        "Sortowanie po terminie rosnąco, z licznikiem dni do terminu.",
        "Dni i pilność liczy serwer przy każdym odczycie, więc nie da się ich rozjechać z kalendarzem.",
        "Wyróżnienia: po terminie, termin dziś, termin jutro, termin wkrótce.",
        "Stan sprawy zmieniany przyciskami; cofnięcie wymaga notatki i zostaje w historii.",
        "Filtr roku, filtra stanu, wyszukiwanie po numerze i przedmiocie, widok miesiąca.",
    ], BLUE, 18)}
  </div>
  <div class="col" style="width:1220px">
    {shot("kalendarz.png", 1220)}
  </div>
</div>
<div class="status-block">
  <div class="status-label">STAN SPRAWY</div>
  <div class="statuses">{st_html}</div>
</div>
"""
    return slide(4, body)


def s05() -> str:
    body = f"""
{kicker("MODUŁY C I D · ARCHIWUM I ŚCIEŻKA URZĘDOWA", SKY)}
{head("Urząd już raz odpowiedział. Wystarczy zapytać.")}
<div class="two-col" style="margin-top:26px;align-items:flex-start">
  <div class="col" style="width:840px">
    <div class="col-label" style="color:{SKY}">ARCHIWUM SPRAW</div>
    {shot("archiwum.png", 840)}
    <div style="margin-top:26px">
    {bullets([
        "49 spraw archiwalnych; wyszukiwanie hybrydowe BM25 + wektory, filtr roku.",
        "Ocena podobieństwa i dopasowane terminy widoczne przy każdym wyniku.",
        "Zamknięcie sprawy dopisuje ją do archiwum, więc baza rośnie z pracą urzędu.",
    ], SKY, 19)}
    </div>
  </div>
  <div class="col" style="width:840px">
    <div class="col-label" style="color:{VIOLET}">ROUTING WYDZIAŁOWY</div>
    {shot("routing.png", 840)}
    <div style="margin-top:26px">
    {bullets([
        "26 komórek organizacyjnych UMB, pewność dopasowania przy każdej sugestii.",
        "Zapytanie z numerem sprawy, datą wpływu i terminem: gotowe do wysłania własnym kanałem.",
        "Nic nie jest wysyłane automatycznie: to projekt pisma, nie wysyłka.",
    ], VIOLET, 19)}
    </div>
  </div>
</div>
{metrics([
    ("5", "wyników w demo, oceny od 0,866 do 0,278", SKY),
    ("7–22 ms", "czas wyszukiwania hybrydowego", BLUE),
    ("95%", "pewność dla Wydziału Organizacji i Kadr", VIOLET),
    ("48%", "pewność dla drugiej sugestii; próg odcina ogon", AMBER),
])}
<div class="callout" style="margin-top:20px">
  <span class="callout-mark" style="background:{SKY}"></span>
  Wyszukiwanie hybrydowe działa na indeksie w SQLite. Bez zewnętrznej wyszukiwarki
  i bez wysyłania dokumentów poza urząd.
</div>
"""
    return slide(5, body)


def s06() -> str:
    body = f"""
{kicker("MODUŁ B · GENERATOR ODPOWIEDZI", AMBER)}
{head("Projekt pisma, w którym każde zdanie ma źródło")}
<div class="two-col" style="margin-top:30px;align-items:flex-start">
  <div class="col" style="width:520px">
    {bullets([
        "Wejście: wniosek, odpowiedzi z wydziałów, archiwum, wgrane ustawy i zarządzenia.",
        "Każde twierdzenie dostaje odnośnik do fragmentu źródła. Zdania bez pokrycia trafiają na osobną listę: nie znikają po cichu.",
        "Podstawa prawna ze zwężonymi zakresami: [2]–[13], nie trzynaście cyfr pod rząd.",
        "Eksport DOCX, PDF i Markdown; nazwa pliku z numerem sprawy.",
        "Na żywym modelu: 4,2–5,6 s na projekt, 5–14 cytowań, zero wiszących odnośników.",
    ], AMBER)}
  </div>
  <div class="col" style="width:1160px">
    {shot("generator.png", 1160)}
  </div>
</div>
{metrics([
    ("4,2–5,6 s", "na projekt pisma, na żywym modelu", AMBER),
    ("5–14", "cytatów źródłowych w jednym projekcie", SKY),
    ("0", "wiszących odnośników; każde zdanie ma źródło", GREEN),
    ("3", "formaty eksportu: DOCX, PDF, Markdown", VIOLET),
])}
"""
    return slide(6, body)


def s07() -> str:
    body = f"""
{kicker("MODUŁ C · ANONIMIZACJA", GREEN)}
{head("Szare, dopóki urzędnik nie zdecyduje. Czarne po akceptacji.")}
<div class="two-col" style="margin-top:30px;align-items:flex-start">
  <div class="col" style="width:520px">
    {bullets([
        "13 kategorii: PESEL, NIP, REGON, dowód, paszport, telefon, e-mail, IBAN, adres, imię i nazwisko, data urodzenia, podpis.",
        "Kolejność detektorów: reguły regex → NER spaCy → przebieg kontekstowy modelu. Regex ma pierwszeństwo na numerach.",
        "Wykryte fragmenty nie są usuwane, dopóki urzędnik ich nie zaakceptuje: pojedynczo albo wszystkie.",
        "Na zbiorze etykietowanym: precyzja 1,00, pełność 1,00, F1 1,00. Zero fałszywych trafień na numerach spraw.",
        "Eksport podaje liczbę usuniętych fragmentów w nagłówku X-Redactions.",
    ], GREEN)}
  </div>
  <div class="col" style="width:1160px">
    {shot("anonimizacja.png", 1160)}
  </div>
</div>
{metrics([
    ("13", "kategorii danych osobowych rozpoznawanych w tekście", GREEN),
    ("1,00", "precyzja na zbiorze etykietowanym", SKY),
    ("1,00", "pełność na zbiorze etykietowanym", BLUE),
    ("0", "fałszywych trafień na numerach spraw", AMBER),
])}
"""
    return slide(7, body)


def s08() -> str:
    users = [
        ("Urzędnicy obsługujący wnioski UDIP", "Codzienna praca, nie projekt IT. Jeden ekran zamiast arkusza i folderów."),
        ("Kierownicy komórek", "Widzą, ile spraw czeka, na czym stoją i kto je prowadzi."),
        ("Biuro Komunikacji Społecznej i redakcja BIP", "Publikacja bez danych osobowych, z policzonymi usunięciami."),
        ("IT miasta", "Jedna instancja, Docker Compose, SQLite, backup jednego pliku."),
    ]
    users_html = "".join(
        f'<div class="user"><div class="user-title">{t}</div>'
        f'<div class="user-text">{d}</div></div>'
        for t, d in users
    )
    roadmap = [
        ("Pilotaż", "Jedna komórka, trzy miesiące, pomiar czasu odpowiedzi przed i po.", BLUE),
        ("Wydział", "Archiwum rośnie o każdą zamkniętą sprawę, więc narzędzie uczy się z pracy urzędu.", SKY),
        ("Cały urząd", "Jedna instancja w serwerowni, model lokalny, zero ruchu na zewnątrz.", VIOLET),
        ("Inne JST", "Ta sama aplikacja, inna taksonomia komórek i inny zestaw ustaw.", GREEN),
    ]
    road_html = "".join(
        f'<div class="road"><span class="road-dot" style="background:{c}"></span>'
        f'<div><div class="road-title">{t}</div><div class="road-text">{d}</div></div></div>'
        for t, d, c in roadmap
    )
    body = f"""
{kicker("DLA KOGO I CO DALEJ", VIOLET)}
{head("Dla urzędników JST. Dziś Bydgoszcz, jutro każdy urząd.")}
<div class="two-col" style="margin-top:34px;align-items:flex-start">
  <div class="col" style="width:820px">
    <div class="col-label" style="color:{BLUE}">DLA KOGO</div>
    {users_html}
  </div>
  <div class="col" style="width:820px">
    <div class="col-label" style="color:{VIOLET}">PRZYSZŁOŚĆ W URZĘDZIE MIASTA</div>
    {road_html}
  </div>
</div>
{cards3([
    ("Czas urzędnika", "Rutynowe pismo powstaje w minutach. Urzędnik czyta i decyduje, zamiast przepisywać.", BLUE),
    ("Jakość obsługi", "Każda odpowiedź ma źródło, a każde usunięcie danych jest policzone i widoczne.", SKY),
    ("Wizerunek miasta", "Bydgoszcz pokazuje rozwiązanie gotowe do wdrożenia w innych JST.", AMBER),
])}
{metrics([
    ("4", "grupy użytkowników w jednym urzędzie", BLUE),
    ("4", "etapy wdrożenia: pilotaż, wydział, cały urząd, inne JST", SKY),
    ("1", "instancja na urząd, w serwerowni miasta", VIOLET),
    ("0", "integracji z SIDAS; nic nie wychodzi poza urząd", GREEN),
])}
<div class="callout" style="margin-top:20px">
  <span class="callout-mark" style="background:{AMBER}"></span>
  Nie zastępuje urzędnika; zdejmuje przepisywanie. Decyzję zawsze podejmuje człowiek,
  a narzędzie nie wysyła niczego samodzielnie i nie integruje się z SIDAS.
</div>
"""
    return slide(8, body)


def s09() -> str:
    groups = [
        (
            "Backend",
            BLUE,
            ["Python 3.12", "FastAPI", "Pydantic v2", "SQLAlchemy 2.0", "SQLite", "structlog"],
        ),
        (
            "Frontend",
            SKY,
            ["React 18", "TypeScript", "Vite", "TanStack Query i Table", "shadcn/ui (Radix)", "TipTap", "Recharts"],
        ),
        (
            "Dokumenty i NLP",
            VIOLET,
            ["pdfplumber", "python-docx", "fpdf2", "spaCy pl_core_news_lg", "BM25 + sqlite-vec"],
        ),
        (
            "Modele",
            AMBER,
            ["Mistral API (obecnie)", "llama.cpp", "Ollama", "protokół OpenAI-compatible"],
        ),
        (
            "Wdrożenie i jakość",
            GREEN,
            ["Docker Compose", "nginx", "pytest", "Vitest", "Playwright", "ruff", "mypy", "eslint"],
        ),
    ]
    cards = "".join(
        f'<div class="tool"><div class="tool-head" style="color:{c}">{name}</div>'
        + "".join(f'<span class="tool-item">{i}</span>' for i in items)
        + "</div>"
        for name, c, items in groups
    )
    body = f"""
{kicker("NARZĘDZIA", AMBER)}
{head("Osiem modułów, dwa adaptery, zero chmury w trybie docelowym")}
<div class="tools">{cards}</div>
<div class="no-block">
  <div class="no-label">CZEGO ŚWIADOMIE NIE MA</div>
  <div class="no-row">
    <div class="no-item"><span class="no-mark"></span>Chmury w trybie docelowym</div>
    <div class="no-item"><span class="no-mark"></span>Zewnętrznego dostawcy tożsamości</div>
    <div class="no-item"><span class="no-mark"></span>Telemetrii i analityki</div>
  </div>
</div>
{metrics([
    ("5", "grup narzędzi: backend, frontend, dokumenty, modele, jakość", AMBER),
    ("2", "języki: Python i TypeScript", BLUE),
    ("100%", "open source, zero płatnych licencji", GREEN),
    ("0", "zależności od chmury w trybie docelowym", RED),
])}
<div class="callout" style="margin-top:20px">
  <span class="callout-mark" style="background:{GREEN}"></span>
  Zgodnie z §11 regulaminu wskazujemy wprost rozwiązania zewnętrzne: bieżący
  prototyp biega na modelu Mistral Small przez API Mistrala. W urzędzie ten sam
  interfejs zasila lokalny, otwarty Bielik 11B v2.3 Instruct (Apache-2.0), a cały
  stos bibliotek jest open source.
</div>
"""
    return slide(9, body)


def s10() -> str:
    body = f"""
{kicker("TRYB ZAMKNIĘTY", GREEN)}
{head("Bez internetu, bez chmury, bez wielkiego modelu")}
<div class="two-col" style="margin-top:30px;align-items:flex-start">
  <div class="col" style="width:820px">
    {bullets([
        "OFFLINE=1 blokuje każde wyjście do sieci: model i embeddingi rzucają OfflineViolation, health raportuje down bez próby połączenia.",
        "Prototyp biega dziś na Mistral Small przez API Mistrala; wagi tego modelu są otwarte (Apache 2.0). Ten sam adapter mówi z llama.cpp i Ollamą na localhost, więc podmiana dostawcy to jedna zmienna.",
        "Baza to jeden plik SQLite; dokumenty, fragmenty i wektory zostają na dysku urzędu.",
        "Brak telemetrii i brak zewnętrznego JWT: token sesji to HMAC-SHA256 ze standardowej biblioteki.",
        "Tryb demo nie potrzebuje żadnego modelu: atrapy z fixtures, deterministyczne.",
    ], GREEN)}
  </div>
  <div class="col" style="width:820px">
    <div class="col-label" style="color:{GREEN}">PROPONOWANY MODEL</div>
    <div class="model-card">
      <div class="model-name">Bielik 11B v2.3 Instruct</div>
      <div class="model-meta">Q4_K_M · 6,7 GB · llama.cpp lub Ollama</div>
      <div class="model-text">Polski model trenowany na tekstach urzędowych. Mieści się
      na jednej maszynie w serwerowni urzędu, bez karty GPU klasy data-center.</div>
    </div>
    <div class="model-alt">
      <b>Alternatywa lżejsza:</b> Qwen2.5 7B Instruct, Q4_K_M, 4,7 GB.
    </div>
    {shot("modele.png", 820)}
  </div>
</div>
<div class="need-block">
  <div class="no-label">CO TRZEBA MIEĆ, ŻEBY TO URUCHOMIĆ</div>
  <div class="need-row">
    <div class="need"><div class="need-title">Serwer w urzędzie</div>
      <div class="need-text">Linux z Dockerem, bez karty GPU klasy data-center.</div></div>
    <div class="need"><div class="need-title">Model na dysku</div>
      <div class="need-text">6,7 GB pobrane raz; potem działa bez sieci.</div></div>
    <div class="need"><div class="need-title">Jedna komenda</div>
      <div class="need-text">Docker Compose stawia frontend, backend i model lokalnie.</div></div>
  </div>
</div>
<div class="closing">
  <span class="closing-text">Odpowiedź w minutach, nie w dniach.</span>
  <span class="closing-sub">Dziękujemy i zapraszamy do prototypu.</span>
</div>
"""
    return slide(10, body)


# ---------------------------------------------------------------- CSS


def css() -> str:
    return f"""
{font_css()}

@page {{ size: 1920px 1080px; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; background: {BG}; }}
body {{ font-family: 'Inter', system-ui, sans-serif; -webkit-font-smoothing: antialiased; }}

.slide {{
  position: relative; width: 1920px; height: 1080px; overflow: hidden;
  background: {BG}; color: {TEXT};
  page-break-after: always; break-after: page;
}}
.slide:last-child {{ page-break-after: auto; break-after: auto; }}
.slide::before {{
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(1000px 640px at 88% -12%, rgba(59,130,246,.20), transparent 68%),
    radial-gradient(760px 520px at -6% 108%, rgba(139,92,246,.14), transparent 70%);
}}
.slide::after {{
  content: ''; position: absolute; inset: 0; pointer-events: none; opacity: .35;
  background-image:
    linear-gradient(to right, rgba(148,163,184,.055) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(148,163,184,.055) 1px, transparent 1px);
  background-size: 96px 96px;
  mask-image: radial-gradient(1200px 800px at 50% 40%, #000 20%, transparent 85%);
}}
.pad {{
  position: absolute; inset: 0; padding: 68px 96px 92px;
  display: flex; flex-direction: column; z-index: 2;
}}

.kicker {{
  display: flex; align-items: center; gap: 14px;
  font-size: 16px; font-weight: 700; letter-spacing: 2.6px; text-transform: uppercase;
}}
.kicker-line {{ width: 30px; height: 3px; border-radius: 2px; display: inline-block; }}

.head {{
  margin: 18px 0 0; font-weight: 700; line-height: 1.1; letter-spacing: -1.4px;
  max-width: 1560px;
}}

.two-col {{ display: flex; gap: 48px; }}
.col {{ display: flex; flex-direction: column; }}

.lead {{ margin: 0 0 26px; font-size: 22px; line-height: 1.55; color: {MUTED}; }}

.bullets {{ list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 15px; }}
.bullets li {{ display: flex; gap: 14px; line-height: 1.45; color: #CBD5E1; }}
.bullets .dot {{ width: 7px; height: 7px; border-radius: 50%; margin-top: 9px; flex: 0 0 7px; }}

.stats {{ display: flex; gap: 18px; }}
.stat {{
  flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px;
  padding: 22px 22px 24px;
}}
.stat-value {{ font-size: 46px; font-weight: 800; letter-spacing: -1.6px; line-height: 1; }}
.stat-label {{ margin-top: 12px; font-size: 16px; line-height: 1.45; color: {MUTED}; }}

.pain {{
  display: flex; gap: 18px; background: {PANEL}; border: 1px solid {BORDER};
  border-radius: 16px; padding: 22px 24px; margin-bottom: 16px;
}}
.pain-bar {{ width: 4px; border-radius: 2px; flex: 0 0 4px; }}
.pain-title {{ font-size: 21px; font-weight: 700; }}
.pain-text {{ margin-top: 8px; font-size: 17px; line-height: 1.5; color: {MUTED}; }}

.ba {{ display: flex; align-items: stretch; gap: 18px; margin-top: 34px; }}
.ba-col {{ flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px; padding: 22px 26px; }}
.ba-before {{ border-color: rgba(239,68,68,.28); }}
.ba-after {{ border-color: rgba(16,185,129,.30); }}
.ba-label {{ font-size: 14px; font-weight: 700; letter-spacing: 2.2px; }}
.ba-text {{ margin-top: 10px; font-size: 18px; line-height: 1.5; color: {MUTED}; }}
.ba-arrow {{ align-self: center; color: #334155; font-size: 26px; }}

.callout {{
  display: flex; align-items: flex-start; gap: 16px;
  background: rgba(59,130,246,.07); border: 1px solid rgba(59,130,246,.22);
  border-radius: 14px; padding: 20px 24px;
  font-size: 19px; line-height: 1.5; color: #CBD5E1;
}}
.callout-mark {{ width: 4px; align-self: stretch; border-radius: 2px; flex: 0 0 4px; }}

.metrics {{ display: flex; gap: 18px; margin-top: auto; }}
.metric {{
  flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px;
  padding: 24px 26px;
}}
.metric-value {{ font-size: 42px; font-weight: 800; letter-spacing: -1.5px; line-height: 1; }}
.metric-label {{ margin-top: 11px; font-size: 16px; line-height: 1.4; color: {MUTED}; }}

.cards3 {{ display: flex; gap: 18px; margin-top: 34px; margin-bottom: 18px; }}
.card3 {{
  flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px;
  padding: 22px 24px;
}}
.card3-title {{ font-size: 20px; font-weight: 700; letter-spacing: -.3px; }}
.card3-text {{ margin-top: 9px; font-size: 17px; line-height: 1.5; color: {MUTED}; }}

.shot {{
  overflow: hidden; border: 1px solid {BORDER}; background: #fff;
  box-shadow: 0 26px 64px rgba(0,0,0,.55);
}}
.shot img {{ display: block; width: 100%; }}

.col-label {{
  font-size: 15px; font-weight: 700; letter-spacing: 2.2px;
  text-transform: uppercase; margin-bottom: 14px;
}}

/* --- slajd 1 --- */
.s-title .pad {{ padding: 0; }}
.title-grid {{ display: flex; height: 100%; }}
.title-left {{
  width: 940px; padding: 0 0 0 96px; display: flex; flex-direction: column;
  justify-content: center;
}}
.title {{
  margin: 26px 0 0; font-size: 92px; font-weight: 800; line-height: 1.02;
  letter-spacing: -3.4px;
}}
.title-sub {{
  margin: 26px 0 0; font-size: 25px; line-height: 1.5; color: {MUTED}; max-width: 720px;
}}
.title-team {{ margin-top: 44px; }}
.title-team-label {{ font-size: 14px; font-weight: 700; letter-spacing: 2.4px; color: {DIM}; }}
.title-team-names {{ margin-top: 10px; font-size: 22px; font-weight: 600; color: #E2E8F0; }}
.chips {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 40px; max-width: 760px; }}
.chip {{
  font-size: 15px; font-weight: 600; color: {MUTED};
  border: 1px solid {BORDER}; border-radius: 999px; padding: 8px 16px;
  background: rgba(148,163,184,.06);
}}
.chip-blue {{ color: #BFDBFE; border-color: rgba(59,130,246,.45); background: rgba(59,130,246,.14); }}
.title-right {{
  flex: 1; display: flex; flex-direction: column; justify-content: center;
  padding-left: 40px; padding-right: 60px;
}}
.title-caption {{
  margin-top: 22px; font-size: 16px; line-height: 1.5; color: {DIM}; max-width: 900px;
}}

/* --- slajd 3 --- */
.steps {{ display: flex; align-items: center; justify-content: center; margin-top: 52px; }}
.step {{
  width: 250px; height: 196px; background: {PANEL}; border: 1px solid {BORDER};
  border-radius: 18px; padding: 26px 24px; position: relative;
}}
.step-bar {{ position: absolute; top: 0; left: 24px; right: 24px; height: 4px; border-radius: 0 0 3px 3px; }}
.step-num {{ font-size: 17px; font-weight: 700; letter-spacing: 2px; }}
.step-title {{ margin-top: 26px; font-size: 27px; font-weight: 700; letter-spacing: -.6px; }}
.step-sub {{ margin-top: 10px; font-size: 17px; color: {DIM}; line-height: 1.4; }}
.step-arrow {{ width: 36px; text-align: center; color: #334155; font-size: 26px; }}

.mods-block {{ margin-top: 46px; }}
.mods-label {{ font-size: 14px; font-weight: 700; letter-spacing: 2.2px; color: {DIM}; }}
.mods {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
.mod {{
  font-size: 16px; color: {MUTED}; border: 1px solid {BORDER}; border-radius: 10px;
  padding: 9px 15px; background: rgba(148,163,184,.05);
}}
.mod b {{ color: #E2E8F0; font-weight: 600; margin-right: 8px; }}

/* --- slajd 4 --- */
.status-block {{ margin-top: auto; }}
.status-label {{ margin-top: 30px; font-size: 14px; font-weight: 700; letter-spacing: 2.2px; color: {DIM}; }}
.status-block .status-label {{ margin-top: 0; }}
.statuses {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }}
.status {{
  font-size: 15px; color: {MUTED}; border: 1px solid {BORDER}; border-radius: 8px;
  padding: 7px 12px; background: rgba(148,163,184,.05);
}}
.status b {{ color: {BLUE}; margin-right: 8px; font-weight: 700; }}

/* --- slajd 8 --- */
.user {{ border-left: 3px solid rgba(59,130,246,.5); padding: 2px 0 2px 18px; margin-bottom: 30px; }}
.user-title {{ font-size: 21px; font-weight: 700; }}
.user-text {{ margin-top: 7px; font-size: 17px; line-height: 1.5; color: {MUTED}; }}

.road {{ display: flex; gap: 16px; margin-bottom: 30px; }}
.road-dot {{ width: 11px; height: 11px; border-radius: 50%; margin-top: 8px; flex: 0 0 11px; }}
.road-title {{ font-size: 21px; font-weight: 700; }}
.road-text {{ margin-top: 7px; font-size: 17px; line-height: 1.5; color: {MUTED}; }}

/* --- slajd 9 --- */
.tools {{ display: flex; gap: 18px; margin-top: 44px; align-items: stretch; }}
.tool {{
  flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 16px;
  padding: 24px 22px; display: flex; flex-direction: column; gap: 9px;
}}
.tool-head {{ font-size: 15px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase; margin-bottom: 6px; }}
.tool-item {{ font-size: 17px; color: #CBD5E1; line-height: 1.35; }}

.no-block {{ margin-top: 34px; }}
.no-label {{ font-size: 14px; font-weight: 700; letter-spacing: 2.2px; color: {DIM}; }}
.no-row {{ display: flex; gap: 16px; margin-top: 14px; }}
.no-item {{
  flex: 1; display: flex; align-items: center; gap: 14px;
  background: rgba(239,68,68,.06); border: 1px solid rgba(239,68,68,.22);
  border-radius: 12px; padding: 16px 20px; font-size: 18px; color: #CBD5E1;
}}
.no-mark {{ width: 4px; align-self: stretch; border-radius: 2px; background: {RED}; flex: 0 0 4px; }}

/* --- slajd 10 --- */
.model-card {{
  background: {PANEL}; border: 1px solid rgba(16,185,129,.35); border-radius: 16px;
  padding: 24px 26px;
}}
.model-name {{ font-size: 30px; font-weight: 700; letter-spacing: -.8px; }}
.model-meta {{ margin-top: 8px; font-size: 17px; color: {GREEN}; font-weight: 600; }}
.model-text {{ margin-top: 14px; font-size: 17px; line-height: 1.5; color: {MUTED}; }}
.model-alt {{ margin: 16px 0 22px; font-size: 17px; color: {MUTED}; }}
.model-alt b {{ color: #E2E8F0; }}

.need-block {{ margin-top: 34px; }}
.need-row {{ display: flex; gap: 16px; margin-top: 14px; }}
.need {{
  flex: 1; background: {PANEL}; border: 1px solid {BORDER}; border-radius: 12px;
  padding: 18px 22px;
}}
.need-title {{ font-size: 19px; font-weight: 700; }}
.need-text {{ margin-top: 7px; font-size: 16px; line-height: 1.45; color: {MUTED}; }}

.closing {{
  margin-top: auto; display: flex; align-items: baseline; gap: 22px;
  border-top: 1px solid {BORDER}; padding-top: 26px;
}}
.closing-text {{ font-size: 40px; font-weight: 800; letter-spacing: -1.4px; }}
.closing-sub {{ font-size: 20px; color: {DIM}; }}

/* --- stopka --- */
.foot {{
  position: absolute; left: 96px; right: 96px; bottom: 34px; z-index: 3;
  display: flex; justify-content: space-between;
  font-size: 14px; color: #475569; letter-spacing: .3px;
}}
.s-title .foot {{ color: #334155; }}
"""


# ---------------------------------------------------------------- złożenie


def build_html() -> str:
    slides = [s01(), s02(), s03(), s04(), s05(), s06(), s07(), s08(), s09(), s10()]
    return (
        "<!doctype html><html lang=\"pl\"><head><meta charset=\"utf-8\">"
        "<title>Capricorn · inteligentny asystent urzędnika · HackNation 2026</title>"
        f"<style>{css()}</style></head><body>{''.join(slides)}</body></html>"
    )


def main() -> int:
    html = build_html()
    out_html = HERE / "prezentacja.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"HTML: {out_html} ({len(html) / 1024 / 1024:.2f} MB)")

    if not CHROME.exists():
        print(f"Brak Chrome: {CHROME}", file=sys.stderr)
        return 1

    out_pdf = HERE / "prezentacja.pdf"
    cmd = [
        str(CHROME),
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        f"--print-to-pdf={out_pdf}",
        out_html.as_uri(),
    ]
    env = {"LD_LIBRARY_PATH": "", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=180)
    if result.returncode != 0:
        print(result.stdout[-3000:], file=sys.stderr)
        print(result.stderr[-3000:], file=sys.stderr)
        return result.returncode

    print(f"PDF:  {out_pdf} ({out_pdf.stat().st_size / 1024 / 1024:.2f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
