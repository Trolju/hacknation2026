# Zasady pracy w tym repozytorium

Ten plik obowiązuje każdego agenta i każdą osobę pracującą nad projektem.
Czytaj go przed pierwszą zmianą.

## Cel

Aplikacja dla Miasta Bydgoszczy: generator odpowiedzi na wnioski o udostępnienie
informacji publicznej (UDIP) z kalendarzem terminów. Szczegóły wymagań:
`ZADANIE-KONKURSOWE.md`. Plan i podział pracy: `PLAN-WDROZENIA.md`.

## Trzy zasady, które czynią pracę równoległą możliwą

### 1. Porty i adaptery

Każdy moduł ma **protokół** w `backend/app/ports/` i dwie implementacje:

- `backend/app/adapters/fakes/` — deterministyczna atrapa czytająca `fixtures/`,
- `backend/app/adapters/real/` — implementacja produkcyjna.

Wybór przez `MODULE_MODE_<NAZWA>=fake|real`, rozstrzygany w
`backend/app/core/container.py`. **Nigdy nie importuj konkretnej klasy adaptera
w routerze ani w serwisie** — bierz zależność przez `Depends(container.get_*)`.

Konsekwencja: możesz pracować nad swoim adapterem, nie czekając na innych.
Dopóki twojego adaptera nie ma, aplikacja działa na atrapie.

### 2. Auto-discovery

- Backend: `backend/app/main.py` skanuje `app/modules/*/router.py` i montuje
  każdy `router: APIRouter` pod `/api/<nazwa>` (albo pod wartość stałej
  `PREFIX` z tego modułu).
- Frontend: `frontend/src/app/registry.ts` skanuje
  `src/features/*/manifest.ts`.

**Nie istnieje centralny rejestr tras.** Dodanie modułu to dodanie katalogu.
Nie edytuj `main.py` ani `registry.ts`, żeby dopisać swój ekran.

### 3. Zamrożony kontrakt

Po Fali 0 te pliki są **tylko do czytania**:

- `contracts/openapi.yaml`
- `contracts/domain.md`
- `backend/app/contracts.py`
- `backend/app/ports/`
- `fixtures/`
- `frontend/src/components/ui/`
- `frontend/src/lib/api.ts`, `frontend/src/lib/query.ts`

Potrzebujesz zmiany w kontrakcie? Otwórz osobny commit z prefiksem
`contract: <opis>` i uzasadnieniem. Zmiana kontraktu wymaga zaktualizowania
`contracts/openapi.yaml`, `backend/app/contracts.py` i typów w
`frontend/src/lib/types.ts` w **jednym** commicie.

## Podział własności

Każdy agent pracuje wyłącznie w swoich katalogach:

| Obszar | Katalogi |
| --- | --- |
| WS1 kalendarz | `backend/app/modules/cases/`, `frontend/src/features/calendar/`, `frontend/src/features/dashboard/` |
| WS2 dokumenty | `backend/app/modules/ingest/`, `backend/app/adapters/real/documents.py`, `frontend/src/features/ingest/` |
| WS3 archiwum | `backend/app/modules/archive/`, `backend/app/adapters/real/archive.py`, `frontend/src/features/archive/` |
| WS4 routing | `backend/app/modules/routing/`, `backend/app/adapters/real/routing.py`, `frontend/src/features/routing/` |
| WS5 generator | `backend/app/modules/drafting/`, `backend/app/adapters/real/drafting.py`, `frontend/src/features/drafting/` |
| WS6 anonimizacja | `backend/app/modules/anonymize/`, `backend/app/adapters/real/anonymize.py`, `frontend/src/features/anonymize/` |
| WS7 modele | `backend/app/adapters/real/inference.py`, `frontend/src/features/settings/` |
| WS8 wdrożenie | `deploy/`, `backend/app/adapters/real/audit.py`, `backend/app/modules/audit/` |
| WS9 UX | `frontend/src/components/` (poza `ui/`), `frontend/src/app/` |

Współdzielone i **nieedytowalne** bez uzgodnienia: `backend/app/core/`,
`backend/app/contracts.py`, `backend/app/ports/`, `contracts/`, `fixtures/`,
`frontend/src/components/ui/`, `frontend/src/lib/`.

## Konwencje

### Backend

- Python 3.12, typy wszędzie, `from __future__ import annotations`.
- Pydantic v2 do DTO; DTO mieszkają w `app/contracts.py`, nie w modułach.
- Błędy przez klasy z `app/core/errors.py` — nigdy `HTTPException` z gołym tekstem.
  Odpowiedź błędu ma kształt `{code, message, details}`, `message` po polsku.
- Daty: `date` dla dni, `datetime` UTC dla znaczników. „Dziś” zawsze z
  `app.core.clock.today()`, nigdy `date.today()`.
- Pola wyliczane (`days_remaining`, `urgency`) zawsze z `app.core.derive`.
- Logowanie przez `structlog`; nigdy nie loguj danych osobowych.
- Testy w `backend/app/modules/<nazwa>/tests/` lub `backend/tests/`.

### Frontend

- TypeScript strict, React 18, funkcje zamiast klas.
- Komponenty UI wyłącznie z `src/components/ui/` (shadcn/ui na Radix).
  Nie pisz własnych prymitywów, jeśli odpowiednik już istnieje.
- Tabele: `DataTable` z `src/components/DataTable.tsx` (TanStack Table).
- Dane: TanStack Query przez hooki z `src/lib/hooks.ts`. Klucze zapytań:
  `["cases", filtry]`, `["case", id]`, `["draft", caseId]`.
- Formularze: React Hook Form + Zod.
- Każdy ekran: `manifest.ts` + `Page.tsx` w `src/features/<nazwa>/`.
- Stany: `LoadingState`, `ErrorState`, `EmptyState` z `src/components/States.tsx`.
- Teksty interfejsu po polsku, bez żargonu technicznego.

### Nazewnictwo

- Pliki Pythona: `snake_case.py`. Pliki TS: `PascalCase.tsx` dla komponentów,
  `camelCase.ts` dla modułów.
- Statusy sprawy: `nowy`, `zapytania_wyslane`, `kwerenda`,
  `przygotowana_odpowiedz`, `odpowiedz_wyslana`.
- Identyfikatory komórek: `waiu`, `wfin`, `bks` itd. — lista w
  `fixtures/departments.json`.

## Definicja ukończenia

Zadanie jest skończone, gdy:

1. `make check` przechodzi (ruff, mypy, pytest, tsc, eslint).
2. Nowe endpointy mają test w `backend/tests/` lub `modules/<nazwa>/tests/`.
3. Nowy ekran ma `manifest.ts` i pojawia się w menu bez edycji rejestru.
4. Aplikacja startuje z `MODULE_MODE_DEFAULT=fake` bez żadnych modeli i sieci.
5. Nie zmieniono plików spoza swojej strefy własności.

## Czego nie robić

- Nie dodawaj zależności bez uzasadnienia w opisie commita.
- Nie zmieniaj `fixtures/` — to dane wejściowe testów i demo.
- Nie usuwaj atrap: są potrzebne do testów i do trybu offline.
- Nie commituj `.env`, `node_modules`, `.venv`, `data/`.
- Nie pisz komentarzy opisujących historię zmian — od tego jest git.
