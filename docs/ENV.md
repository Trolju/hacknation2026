# Zmienne środowiskowe

Konfiguracja idzie przez zmienne środowiskowe albo plik `.env`. Wszystkie
pola mają wartości domyślne, więc pusty plik też wystartuje.

| Gdzie | Kiedy |
| --- | --- |
| `backend/.env` | uruchomienie lokalne (`scripts/start-local.sh`, `make backend`) |
| `deploy/.env` | docker (`docker compose -f deploy/docker-compose.yml`) |

Oba pliki są w `.gitignore`. Backend czyta `.env` z katalogu, w którym
startuje — dlatego `start-local.sh` wchodzi do `backend/`.

## Templatka

Skopiuj do `backend/.env` i uzupełnij to, czego potrzebujesz:

```dotenv
# ── tryb modułów ──────────────────────────────────────────────────────────
# fake = deterministyczne atrapy z fixtures/, bez modeli i bez sieci
# real = implementacje z backend/app/adapters/real/
MODULE_MODE_DEFAULT=real

# Nadpisanie pojedynczego modułu. Nazwy: CASES, INGEST, ARCHIVE, ROUTING,
# DRAFTING, ANONYMIZE, INFERENCE, AUDIT.
# MODULE_MODE_CASES=fake
# MODULE_MODE_ARCHIVE=fake

# Embeddingi zostają na atrapie: LocalEmbedding mówi protokołem /embeddings,
# a Mistral nie serwuje modelu BAAI/bge-m3. Archiwum działa bez nich —
# zostaje BM25 i pokrycie leksykalne.
MODULE_MODE_INFERENCE_EMBEDDING=fake

# ── dane ──────────────────────────────────────────────────────────────────
DATABASE_URL=sqlite:///./data/app.db
# FIXTURES_DIR=/ścieżka/do/fixtures
# UPLOAD_DIR=./data/uploads

# ── demo i terminy ────────────────────────────────────────────────────────
# Kotwica "dziś" dla danych demonstracyjnych. Pusta wartość to błąd
# walidacji — albo data, albo usuń linię.
DEMO_TODAY=2026-03-16

# Ustawowy termin odpowiedzi na wniosek (art. 13 ust. 1 UDIP).
DEFAULT_RESPONSE_DAYS=14

# true blokuje wszystkie połączenia sieciowe.
OFFLINE=false

# ── model językowy ────────────────────────────────────────────────────────
# fake     — atrapa, bez modelu (tryb demo)
# mistral  — Mistral La Plateforme (chmura)
# llamacpp — lokalny serwer llama.cpp (docelowy tryb urzędu)
# ollama   — lokalny Ollama
# openai   — dowolny serwer zgodny z OpenAI
LLM_PROVIDER=fake
LLM_MODEL=Bielik-11B-v2.3-Instruct
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=
LLM_TIMEOUT_S=60
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.2

# ── embeddingi ────────────────────────────────────────────────────────────
EMBEDDING_PROVIDER=fake
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=384

# ── upload ────────────────────────────────────────────────────────────────
# Limit rozmiaru wgrywanego pliku w bajtach (10 MB).
MAX_UPLOAD_BYTES=10485760

# ── CORS ──────────────────────────────────────────────────────────────────
# Lista w formacie JSON, nie po przecinku.
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# ── uwierzytelnianie ──────────────────────────────────────────────────────
# Klucz do podpisywania tokenów sesji (HMAC-SHA256). Pusty = losowy przy
# każdym starcie, więc po restarcie wszyscy logują się ponownie.
# W demo wpisz stałą wartość.
AUTH_SECRET=
AUTH_SESSION_HOURS=8
# false wyłącza logowanie. Inicjały w sprawach biorą się wtedy z pierwszego
# użytkownika fixtures/users.json.
AUTH_ENABLED=true
```

## Trzy gotowe profile

**Demo offline** — bez sieci, bez modeli, wszystko z `fixtures/`:

```dotenv
MODULE_MODE_DEFAULT=fake
LLM_PROVIDER=fake
OFFLINE=true
DEMO_TODAY=2026-03-16
AUTH_ENABLED=true
AUTH_SECRET=demo-staly-klucz
```

**Demo z modelem w chmurze** — pełna ścieżka, odpowiedzi generowane naprawdę:

```dotenv
MODULE_MODE_DEFAULT=real
MODULE_MODE_INFERENCE_EMBEDDING=fake
LLM_PROVIDER=mistral
LLM_MODEL=mistral-small-latest
LLM_API_KEY=<klucz z console.mistral.ai>
DEMO_TODAY=2026-03-16
AUTH_ENABLED=true
AUTH_SECRET=demo-staly-klucz
```

**Docelowy tryb urzędu** — bez chmury, model lokalny:

```dotenv
MODULE_MODE_DEFAULT=real
LLM_PROVIDER=llamacpp
LLM_MODEL=Bielik-11B-v2.3-Instruct
LLM_BASE_URL=http://localhost:8080/v1
OFFLINE=true
```

Mistral Small 3.1 (24B, Apache 2.0) to ten sam model, który działa lokalnie
przez llama.cpp — zmienia się wtedy tylko `LLM_PROVIDER` i `LLM_BASE_URL`.

## Wszystkie zmienne

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `MODULE_MODE_DEFAULT` | `fake` | tryb wszystkich modułów: `fake` albo `real` |
| `MODULE_MODE_<NAZWA>` | — | tryb jednego modułu, nadpisuje powyższe |
| `MODULE_MODE_INFERENCE_EMBEDDING` | — | tryb embeddingów, w praktyce zawsze `fake` |
| `DATABASE_URL` | `sqlite:///./data/app.db` | baza; w dockerze `sqlite:////srv/data/app.db` |
| `FIXTURES_DIR` | `<repo>/fixtures` | dane demonstracyjne i testowe |
| `UPLOAD_DIR` | `data/uploads/` | katalog wgranych plików |
| `DEMO_TODAY` | `2026-03-16` | kotwica „dziś”; pusta wartość to błąd walidacji |
| `DEFAULT_RESPONSE_DAYS` | `14` | ustawowy termin odpowiedzi |
| `OFFLINE` | `false` | `true` blokuje połączenia sieciowe |
| `LLM_PROVIDER` | `fake` | `fake`, `mistral`, `llamacpp`, `ollama`, `openai` |
| `LLM_MODEL` | `Bielik-11B-v2.3-Instruct` | nazwa modelu |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | endpoint zgodny z OpenAI |
| `LLM_API_KEY` | pusty | klucz, jeśli dostawca go wymaga |
| `LLM_TIMEOUT_S` | `60` | timeout pojedynczego wywołania |
| `LLM_MAX_TOKENS` | `2048` | limit tokenów odpowiedzi |
| `LLM_TEMPERATURE` | `0.2` | temperatura próbkowania |
| `EMBEDDING_PROVIDER` | `fake` | `fake`, `local`, `openai` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | nazwa modelu embeddingów |
| `EMBEDDING_DIM` | `384` | wymiar wektora |
| `MAX_UPLOAD_BYTES` | `10485760` | limit wgrywanego pliku (10 MB) |
| `CORS_ORIGINS` | `["http://localhost:5173", ...]` | dozwolone originy, JSON |
| `AUTH_SECRET` | pusty | klucz HMAC; pusty = losowy przy starcie |
| `AUTH_SESSION_HOURS` | `8` | ważność sesji |
| `AUTH_ENABLED` | `true` | `false` wyłącza logowanie |
| `APP_PORT` | `8080` | port interfejsu w dockerze (tylko `deploy/.env`) |
| `ENV_FILE` | `.env` | nazwa pliku konfiguracji; pusty wyłącza czytanie |

Nazwy modułów do `MODULE_MODE_<NAZWA>`: `CASES`, `INGEST`, `ARCHIVE`,
`ROUTING`, `DRAFTING`, `ANONYMIZE`, `INFERENCE`, `AUDIT`.

## Rzeczy, które zaskakują

**`DEMO_TODAY` nie może być pusty.** Pusta wartość to błąd walidacji przy
starcie. Chcesz prawdziwą datę — usuń linię, nie zostawiaj `DEMO_TODAY=`.

**`AUTH_SECRET` pusty znaczy losowy.** Tokeny przestają być ważne po każdym
restarcie backendu. W demo wpisz stałą wartość, żeby nie logować się co chwilę.

**`CORS_ORIGINS` to JSON.** `http://a,http://b` nie zadziała, potrzebne jest
`["http://a","http://b"]`.

**`MODULE_MODE_*` działa też z pliku.** Pydantic wczytuje tylko zadeklarowane
pola, a tryby modułów są dynamiczne — dlatego `settings.py` doczytuje `.env`
osobno. Zmienna środowiskowa ma pierwszeństwo nad plikiem.

**Brak adaptera realnego nie wywala aplikacji.** Kontener loguje
`adapter_real_missing` i wraca do atrapy. Dlatego `MODULE_MODE_DEFAULT=real`
jest bezpieczne nawet w połowie pracy. Stan faktyczny: `/api/health`
i `/api/meta`.

**W dockerze host to `host.docker.internal`.** Lokalny model na porcie 11434
wymaga `LLM_BASE_URL=http://host.docker.internal:11434/v1`, nie `localhost`.

## Sprawdzenie, co faktycznie działa

```bash
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool
```

Odpowiedź zawiera mapę `modules` z trybem każdego modułu. To jedyne źródło
prawdy — plik `.env` mówi, co chciałeś, `/api/health` mówi, co wstało.
