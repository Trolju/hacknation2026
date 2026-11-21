# Inteligentny asystent urzędnika

Generator odpowiedzi na wnioski o udostępnienie informacji publicznej (UDIP)
z kalendarzem terminów, dla Miasta Bydgoszczy. Projekt konkursowy HackNation 2026.

## Co robi aplikacja

Osiem ekranów, jedna ścieżka: od wgranego wniosku do wysłanej odpowiedzi.

| Ekran | Ścieżka | Co daje |
| --- | --- | --- |
| Pulpit | `/` | zaległości, terminy dzisiejsze, najbliższe dni, ostatnio zamknięte sprawy |
| Kalendarz terminów | `/kalendarz` | wszystkie wnioski według terminu 14 dni, filtry, widok miesiąca, zmiana stanu, przedłużenie terminu w kwerendzie |
| Dokumenty | `/dokumenty` | wgranie wniosku w PDF/DOCX, odczyt tekstu, baza wiedzy z fragmentami |
| Archiwum spraw | `/archiwum` | wyszukanie podobnych spraw i wcześniejszych rozstrzygnięć |
| Routing wydziałowy | `/wydzialy` | wskazanie komórek organizacyjnych i treść zapytania |
| Generator odpowiedzi | `/odpowiedzi` | projekt odpowiedzi z cytowaniami, edycją i eksportem DOCX/PDF/MD |
| Anonimizacja | `/anonimizacja` | usunięcie danych osobowych przed publikacją |
| Ustawienia | `/ustawienia` | tryb każdego modułu, stan modelu, wersja i tryb offline |

Dzwonek w górnym pasku pokazuje wnioski po terminie, na dziś i na jutro —
lista liczy się przy odczycie, więc nie ma joba w tle ani stanu do rozjechania.

**Archiwum rośnie wraz z pracą urzędu.** Zamknięcie wniosku (stan
`odpowiedz_wyslana`) dopisuje go do archiwum razem z gotową odpowiedzią, więc
kolejny podobny wniosek znajdzie już sprawy załatwione w aplikacji, nie tylko
te z `fixtures/`. Wgrane ustawy i zarządzenia (rodzaj `ustawa` /
`zarzadzenie`) wchodzą do podstawy prawnej projektu; wgrany akt o tym samym
tytule co plik z `fixtures/statutes/` przykrywa go — tak działa aktualizacja
ustawy.

## Szybki start

Wymagania: Python 3.12, Node 20+, `uv`.

```bash
make install          # zależności backendu i frontendu
make backend          # http://127.0.0.1:8000  (docs: /api/docs)
make frontend         # http://127.0.0.1:5173
```

Aplikacja startuje w trybie `fake`: wszystkie moduły odpowiadają na podstawie
danych z `fixtures/`, bez modeli językowych i bez dostępu do sieci.

## Demo

```bash
scripts/demo.sh       # czyści data/, ustawia tryb fake i DEMO_TODAY, uruchamia oba serwery
scripts/stop-local.sh # zatrzymuje
```

Skrypt wypisuje adresy i listę „co pokazać”. Scenariusz przejścia przez aplikację
(8 minut, krok po kroku, z numerami spraw i identyfikatorami komórek) leży
w `docs/DEMO.md`.

Flagi `demo.sh`: `--backend-only`, `--frontend-only`, `--no-reset` (nie czyści
`backend/data/`), `--help`. Porty zmienia się zmiennymi `BACKEND_PORT`
i `FRONTEND_PORT`.

## Struktura

```
contracts/          zamrożony kontrakt API i słownik domeny
fixtures/           dane demonstracyjne i testowe (read-only)
backend/app/
  core/             konfiguracja, zegar, błędy, kontener zależności
  contracts.py      DTO (Pydantic v2)
  ports/            protokoły modułów
  adapters/fakes/   atrapy deterministyczne
  adapters/real/    implementacje produkcyjne
  modules/<nazwa>/  router, serwis, modele, testy
backend/tests/      testy przekrojowe i end-to-end
frontend/src/
  app/              powłoka aplikacji, rejestr ekranów
  components/ui/    shadcn/ui (Radix)
  features/<nazwa>/ manifest.ts + Page.tsx
  lib/              klient API, hooki, formatowanie
scripts/            start-local.sh, stop-local.sh, demo.sh
docs/               DEMO.md
deploy/             uruchomienie produkcyjne
```

## Tryby modułów

Osiem modułów (`cases`, `ingest`, `archive`, `routing`, `drafting`, `anonymize`,
`inference`, `audit`) działa niezależnie w trybie `fake` albo `real`:

```bash
MODULE_MODE_DEFAULT=fake          # wszystko na atrapach
MODULE_MODE_ARCHIVE=real          # tylko archiwum na implementacji realnej
```

Brakujący adapter realny nie wywala aplikacji — kontener loguje ostrzeżenie
i wraca do atrapy. Aktualny tryb każdego modułu widać w „Ustawieniach”
oraz w `GET /api/health`.

Pozostałe zmienne: `DEMO_TODAY` (kotwica „dziś” dla fixtures, domyślnie
`2026-03-16`), `DATABASE_URL` (domyślnie `sqlite:///./data/app.db`),
`UPLOAD_DIR` (domyślnie `data/uploads/`), `OFFLINE=1`.

## Testy

```bash
make test        # backend (pytest) + frontend (vitest)
make check       # ruff + eslint, mypy + tsc, testy
make build       # produkcyjny build frontendu
```

Test end-to-end całej ścieżki urzędnika — wszystkie moduły w trybie `real`,
jedenaście kroków przez HTTP:

```bash
cd backend && .venv/bin/python -m pytest tests/test_e2e_flow.py -q
```

## Dokumentacja

- `docs/DEMO.md` — scenariusz demo krok po kroku
- `ZADANIE-KONKURSOWE.md` — treść zadania w ujednoliconej formie
- `PLAN-WDROZENIA.md` — architektura, podział pracy, fale
- `AGENTS.md` — zasady pracy równoległej i strefy własności
- `contracts/domain.md` — słownik pól, maszyna stanów, reguły scalania
- `contracts/openapi.yaml` — powierzchnia API
