# Narzędzia i biblioteki

Spis wszystkiego, na czym stoi Capricorn: czego wymaga aplikacja, czego
wymagają testy, co buduje film i prezentację. Wersje sprawdzone na maszynie,
na której projekt powstał.

## W skrócie

| Warstwa | Technologia |
| --- | --- |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite |
| Frontend | React 18, TypeScript 5.7, Vite 6, Tailwind 3, shadcn/ui |
| Modele | Mistral Small (chmura), Bielik 11B v2.3 (docelowo lokalnie) |
| Wdrożenie | Docker, nginx, docker compose |
| Film | Revideo 0.10.4, ffmpeg, Voxtral TTS |
| Prezentacja | Python + chrome-headless-shell |

## Wymagania systemowe

| Narzędzie | Wersja sprawdzona | Do czego |
| --- | --- | --- |
| Python | 3.12.13 | backend, testy, skrypty |
| Node.js | 26.11.1 (wymagane 20+) | frontend, film |
| npm | 12.2.1 | zależności frontendu |
| `uv` | 0.11.26 | środowisko i pakiety Pythona |
| Docker Engine | 29.10.0 | wdrożenie kontenerowe |
| Docker Compose | 5.8.0 | orkiestracja dwóch usług |
| `make` | — | skróty deweloperskie |

Python 3.12 jest wymagany, nie „mile widziany": `pyproject.toml` deklaruje
`requires-python = ">=3.12"`, a kod używa składni `X | None` w adnotacjach
bez `from __future__` w części modułów.

## Backend

Zależności produkcyjne z `backend/pyproject.toml`:

| Pakiet | Rola |
| --- | --- |
| `fastapi` | warstwa HTTP, auto-dokumentacja OpenAPI |
| `uvicorn[standard]` | serwer ASGI |
| `pydantic` v2 | DTO i walidacja |
| `pydantic-settings` | konfiguracja z `.env` i zmiennych środowiskowych |
| `sqlalchemy` 2 | ORM, SQLite jako baza |
| `python-multipart` | wgrywanie plików |
| `structlog` | logi strukturalne |
| `httpx` | klient HTTP do modeli i embeddingów |
| `python-dateutil` | liczenie terminów ustawowych |

Grupa `documents` — obsługa plików, bez niej nie działa wgrywanie wniosków:

| Pakiet | Rola |
| --- | --- |
| `pdfplumber` | odczyt tekstu z PDF |
| `python-docx` | odczyt i zapis DOCX |
| `fpdf2` | eksport odpowiedzi do PDF |

Grupa `ai` — opcjonalna, nieużywana w trybie demo:

| Pakiet | Rola |
| --- | --- |
| `spacy` | NER do anonimizacji |
| `sentence-transformers` | embeddingi lokalne |

Grupa `dev`:

| Pakiet | Rola |
| --- | --- |
| `pytest` + `pytest-asyncio` | testy, tryb `asyncio_mode = "auto"` |
| `ruff` | lint i formatowanie, linia 100 znaków |
| `mypy` | typy, `check_untyped_defs = true` |

## Frontend

Zależności z `frontend/package.json`. Interfejs stoi na sprawdzonych
bibliotekach, nie na rozwiązaniach pisanych od zera.

**Rdzeń**

| Pakiet | Rola |
| --- | --- |
| `react` 18 + `react-dom` | UI |
| `react-router-dom` 6 | routing |
| `typescript` 5.7 | typy |
| `vite` 6 | dev server i build |
| `tailwindcss` 3 + `tailwindcss-animate` | stylowanie |
| `tailwind-merge`, `clsx`, `class-variance-authority` | składanie klas i wariantów |

**Komponenty — shadcn/ui na Radix**

`@radix-ui/react-*`: `alert-dialog`, `checkbox`, `dialog`, `dropdown-menu`,
`label`, `popover`, `progress`, `scroll-area`, `select`, `separator`, `slot`,
`tabs`, `tooltip`. shadcn/ui to nie paczka, a wzorce kopiowane do
`frontend/src/components/ui/` — dlatego te pliki są zamrożone i nie edytuje się
ich bez powodu.

**Dane i formularze**

| Pakiet | Rola |
| --- | --- |
| `@tanstack/react-query` 5 | pobieranie i cache stanu serwera |
| `@tanstack/react-table` 8 | tabele z sortowaniem i filtrami |
| `react-hook-form` + `@hookform/resolvers` + `zod` | formularze i walidacja |
| `@tiptap/react` + `starter-kit`, `highlight`, `placeholder` | edytor projektu odpowiedzi |

**Reszta**

| Pakiet | Rola |
| --- | --- |
| `recharts` | wykresy na pulpicie |
| `date-fns` 4 | formatowanie dat |
| `react-day-picker` 9 | kalendarz miesięczny |
| `cmdk` | paleta poleceń |
| `sonner` | powiadomienia |
| `lucide-react` | ikony |

**Narzędzia**

| Pakiet | Rola |
| --- | --- |
| `vitest` 2 | testy jednostkowe |
| `eslint` 9 + `typescript-eslint` | lint |
| `@vitejs/plugin-react` | integracja React z Vite |
| `postcss`, `autoprefixer` | pipeline CSS |

## Modele

| Model | Gdzie | Do czego |
| --- | --- | --- |
| `mistral-small-latest` | Mistral La Plateforme | generowanie odpowiedzi, tryb hackathonowy |
| `Bielik-11B-v2.3-Instruct` | llama.cpp / Ollama | docelowy tryb urzędu, bez sieci |
| `voxtral-mini-tts-3-0` | Mistral API | lektor filmu, głos `voice_3154` (Leon) |
| `BAAI/bge-m3` | — | embeddingi; atrapa, bo Mistral nie serwuje tego modelu |

Mistral Small 3.1 (24B, Apache 2.0) to ten sam model, który da się uruchomić
lokalnie przez llama.cpp — zmienia się wtedy tylko `LLM_PROVIDER`
i `LLM_BASE_URL`. Dlatego przejście z chmury na serwer urzędu nie wymaga
zmian w kodzie.

## Wdrożenie

| Narzędzie | Rola |
| --- | --- |
| Docker Engine | kontenery |
| Docker Compose | dwie usługi: `backend`, `frontend` |
| `nginx:alpine` | serwowanie builda Vite, proxy `/api`, nagłówki bezpieczeństwa |
| `python:3.12-slim` | obraz backendu, użytkownik `app` (uid 10001) |
| `node:20-alpine` | etap budowania frontendu |

## Film i prezentacja

Te narzędzia nie są potrzebne do uruchomienia aplikacji. Oba katalogi są
w `.gitignore` — zostają lokalnie.

| Narzędzie | Rola |
| --- | --- |
| Revideo 0.10.4 | generator filmu, odpowiednik Remotion (MIT) |
| `@ffmpeg-installer` / `@ffprobe-installer` | ffmpeg i ffprobe bez instalacji systemowej |
| Puppeteer | render scen w przeglądarce |
| Voxtral TTS | lektor polski |
| `chrome-headless-shell` | zrzuty ekranu do prezentacji |
| `python-docx`-owy `build.py` | składanie `prezentacja.html` i `.pdf` |

## Jak to było budowane

Projekt powstał w Mistral Vibe — agencie CLI pracującym na repozytorium.
Podział pracy i strefy własności opisuje `AGENTS.md`, architekturę
i kolejność fal `PLAN-WDROZENIA.md`. Trzy zasady, które pozwoliły pracować
wielu agentom naraz bez konfliktów:

1. **Porty i adaptery** — każdy moduł ma protokół w `backend/app/ports/`
   i dwie implementacje. Router nie importuje konkretnej klasy, bierze
   zależność z kontenera.
2. **Auto-discovery** — `main.py` skanuje `app/modules/*/router.py`,
   `registry.ts` skanuje `src/features/*/manifest.ts`. Nie ma centralnego
   rejestru tras, więc dodanie modułu to dodanie katalogu.
3. **Zamrożony kontrakt** — `contracts/openapi.yaml` i `contracts/domain.md`
   są niezmienne; zmiana wymaga osobnej decyzji, nie przypadkowej edycji.

## Sprawdzenie, że narzędzia są na miejscu

```bash
python3 --version        # 3.12.x
node --version           # v20.x lub nowszy
uv --version
docker compose version
make --version
```

W tym środowisku Node wymaga czystego `LD_LIBRARY_PATH`:

```bash
env -u LD_LIBRARY_PATH node --version
```

Skrypty w `scripts/` i `Makefile` robią to same.
