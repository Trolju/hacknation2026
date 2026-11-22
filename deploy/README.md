# Wdrożenie — Capricorn

Instrukcja dla osoby, która widzi to repozytorium pierwszy raz. Po jej
przejściu aplikacja działa lokalnie (bez dockera) albo w dockerze.

Aplikacja to generator odpowiedzi na wnioski o udostępnienie informacji
publicznej (UDIP) z kalendarzem terminów. Domyślnie startuje w trybie `fake`:
wszystkie moduły odpowiadają na podstawie danych z `fixtures/`, bez modeli
językowych i bez dostępu do sieci.

---

## 1. Wymagania

| Wariant | Potrzebne |
| --- | --- |
| Lokalnie | Python 3.12, Node 20+, `uv` (albo `pip` + `venv`), `curl` |
| Docker | Docker Engine 24+ z Compose v2 (`docker compose version`) |

Sprawdzenie:

```bash
python3 --version    # 3.12.x
node --version       # v20.x lub nowszy
docker compose version
```

Jeśli dockera nie ma:

```bash
# Arch / CachyOS
sudo pacman -S docker docker-compose docker-buildx
# Debian / Ubuntu
sudo apt install docker.io docker-compose-v2

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # potem wyloguj się i zaloguj ponownie
```

Bez grupy `docker` każda komenda kończy się `permission denied while trying to
connect to the docker API`. Dodanie do grupy działa dopiero w nowej sesji.

---

## 2. Uruchomienie lokalne (bez dockera)

### 2.1. Zależności — raz

```bash
make install
```

Równoważnik ręczny, jeśli nie ma `make` ani `uv`:

```bash
cd backend
python3.12 -m venv .venv
# Projekt nie jest paczką instalowalną (tool.uv.package = false), więc
# `pip install .` nie zadziała — zależności bierzemy wprost z pyproject.toml.
python3 -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/req.txt
.venv/bin/pip install -r /tmp/req.txt
.venv/bin/pip install pytest pytest-asyncio ruff mypy pdfplumber python-docx fpdf2

cd ../frontend
npm install --no-audit --no-fund
```

### 2.2. Start

```bash
scripts/start-local.sh
```

Skrypt:

1. uruchamia backend (`uvicorn app.main:app`) w tle na `127.0.0.1:8000`,
2. czeka, aż `/api/health` odpowie `200`,
3. uruchamia frontend (Vite) na `127.0.0.1:5173`,
4. wypisuje adresy i ścieżki logów.

Oba procesy są odczepione od terminala (`setsid`), więc przeżywają zamknięcie
okna. Logi: `.run/backend.log`, `.run/frontend.log`. PID-y: `.run/*.pid`.

Warianty:

```bash
scripts/start-local.sh --backend-only    # tylko API
scripts/start-local.sh --frontend-only   # tylko interfejs
RELOAD=1 scripts/start-local.sh          # backend z auto-przeładowaniem
BACKEND_PORT=9000 scripts/start-local.sh # inny port
scripts/start-local.sh --help
```

### 2.3. Sprawdzenie, że działa

```bash
curl -i http://127.0.0.1:8000/api/health
# HTTP/1.1 200 OK
# {"status":"ok","version":"0.1.0","modules":{"cases":"fake",...}}

curl -s http://127.0.0.1:8000/api/audit
# []  — dziennik audytu (pusty, dopóki nic nie zapisano)

curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5173/
# 200
```

- Interfejs: <http://127.0.0.1:5173>
- Dokumentacja API (Swagger): <http://127.0.0.1:8000/api/docs>
- Kontrakt: <http://127.0.0.1:8000/api/openapi.json>

### 2.4. Zatrzymanie

```bash
scripts/stop-local.sh
```

Warianty: `--backend-only`, `--frontend-only`.

### 2.5. Alternatywa: `make`

```bash
make backend     # uvicorn w pierwszym planie, z --reload
make frontend    # vite w pierwszym planie
```

Dwa osobne terminale. `make` nie odczepia procesów — zamykasz je `Ctrl+C`.

---

## 3. Uruchomienie w dockerze

### 3.1. Konfiguracja — raz

```bash
cp deploy/.env.example deploy/.env
```

Plik `deploy/.env` jest w `.gitignore`. Bez niego `docker compose` przerwie
pracę komunikatem o brakującym pliku — to celowe, żeby nikt nie uruchomił
produkcji z domyślnymi ustawieniami przez przypadek.

### 3.2. Start

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Pierwszy build trwa kilka minut (pobranie obrazów bazowych, `npm ci`,
`pip install`). Kolejne starty są szybkie.

### 3.3. Sprawdzenie

```bash
curl -i http://localhost:8080/api/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/
```

Interfejs: <http://localhost:8080>. Port zmienisz przez `APP_PORT` w `deploy/.env`.

### 3.4. Codzienna obsługa

```bash
docker compose -f deploy/docker-compose.yml ps          # stan usług
docker compose -f deploy/docker-compose.yml logs -f     # logi
docker compose -f deploy/docker-compose.yml down        # stop (dane zostają)
docker compose -f deploy/docker-compose.yml down -v     # stop + usunięcie danych
```

### 3.5. Co powstaje

| Element | Opis |
| --- | --- |
| `capricorn-backend` | FastAPI + uvicorn, użytkownik `app` (uid 10001), nie-root |
| `capricorn-frontend` | nginx z buildem Vite, proxy `/api` do backendu |
| wolumen `app-data` | `/srv/data` — baza SQLite i wgrane pliki |

Backend ma `HEALTHCHECK` na `/api/health`; frontend startuje dopiero, gdy
backend jest zdrowy (`depends_on: condition: service_healthy`).

### 3.6. Kopia zapasowa danych

Wszystko, co trzeba zachować, leży w wolumenie `app-data`:

```bash
docker run --rm -v capricorn_app-data:/data -v "$PWD":/backup alpine \
    tar czf /backup/capricorn-dane-$(date +%F).tar.gz -C /data .
```

Odtworzenie: podmiana wolumenu w ten sam sposób (`tar xzf`).

---

## 4. Zmienne środowiskowe

Ustawiane w `deploy/.env` (docker) albo `backend/.env` (lokalnie — backend
czyta `.env` z katalogu, w którym startuje). Wszystkie są opcjonalne.

| Zmienna | Domyślnie | Znaczenie |
| --- | --- | --- |
| `APP_PORT` | `8080` | port interfejsu w dockerze |
| `MODULE_MODE_DEFAULT` | `fake` | tryb wszystkich modułów: `fake` albo `real` |
| `MODULE_MODE_<NAZWA>` | — | tryb jednego modułu, nadpisuje powyższe |
| `OFFLINE` | `false` | `true` blokuje połączenia sieciowe |
| `DATABASE_URL` | `sqlite:///./data/app.db` | baza; w dockerze `sqlite:////srv/data/app.db` |
| `FIXTURES_DIR` | `<repo>/fixtures` | dane demonstracyjne |
| `DEFAULT_RESPONSE_DAYS` | `14` | ustawowy termin odpowiedzi (art. 13 ust. 1 UDIP) |
| `DEMO_TODAY` | `2026-03-16` | kotwica „dziś” dla danych demo; pusta wartość to błąd |
| `MAX_UPLOAD_BYTES` | `10485760` | limit wgrywanego pliku (10 MB) |
| `CORS_ORIGINS` | `["http://localhost:5173", ...]` | dozwolone originy (JSON) |
| `LLM_PROVIDER` | `fake` | `fake`, `openai`, `llamacpp`, `ollama` |
| `LLM_MODEL` | `Bielik-11B-v2.3-Instruct` | nazwa modelu |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | endpoint zgodny z OpenAI |
| `LLM_API_KEY` | pusty | klucz, jeśli dostawca go wymaga |
| `LLM_TIMEOUT_S` | `60` | timeout pojedynczego wywołania |
| `EMBEDDING_PROVIDER` | `fake` | `fake`, `local`, `openai` |

Nazwy modułów do `MODULE_MODE_<NAZWA>`: `CASES`, `INGEST`, `ARCHIVE`,
`ROUTING`, `DRAFTING`, `ANONYMIZE`, `INFERENCE`, `AUDIT`.

---

## 5. Przełączanie modułów na `real`

Każdy moduł ma protokół w `backend/app/ports/` i dwie implementacje:
atrapę w `backend/app/adapters/fakes/` oraz implementację produkcyjną
w `backend/app/adapters/real/`. Kontener (`backend/app/core/container.py`)
wybiera jedną na podstawie zmiennej środowiskowej.

### 5.1. Wszystko naraz

```bash
MODULE_MODE_DEFAULT=real scripts/start-local.sh
```

albo w `deploy/.env`:

```dotenv
MODULE_MODE_DEFAULT=real
```

### 5.2. Pojedynczy moduł

```bash
MODULE_MODE_AUDIT=real scripts/start-local.sh
```

albo w `deploy/.env`:

```dotenv
MODULE_MODE_DEFAULT=fake
MODULE_MODE_AUDIT=real
MODULE_MODE_CASES=real
```

### 5.3. Co się dzieje, gdy adaptera nie ma

Kontener loguje ostrzeżenie `adapter_real_missing` i wraca do atrapy.
Aplikacja nigdy nie przestaje działać z powodu brakującego modułu — dlatego
`MODULE_MODE_DEFAULT=real` jest bezpieczne nawet w trakcie rozwoju.

Stan faktyczny widać w `/api/health` i `/api/meta`:

```bash
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool
```

### 5.4. Sprawdzenie, że moduł naprawdę jest realny

```bash
MODULE_MODE_AUDIT=real scripts/start-local.sh --backend-only
curl -s http://127.0.0.1:8000/api/health | grep -o '"audit":"[a-z]*"'
# "audit":"real"
```

---

## 6. Dziennik audytu

Dziennik jest tylko dopisywany: tabela `audit_entries` w SQLite, bez
aktualizacji i usuwania (blokują je wyzwalacze bazy). Schemat tworzy się sam
przy pierwszym zapisie.

```bash
# włącz implementację realną
MODULE_MODE_AUDIT=real scripts/start-local.sh --backend-only

# odczyt
curl -s "http://127.0.0.1:8000/api/audit?limit=20" | python3 -m json.tool
curl -s "http://127.0.0.1:8000/api/audit?case_id=<uuid>" | python3 -m json.tool
```

Parametry: `case_id` (filtr po sprawie), `limit` (1–500, domyślnie 100).
Wpisy wracają od najnowszego.

Zapis zdarzeń z poziomu kodu opisuje `backend/app/modules/audit/INTEGRACJA.md`.

---

## 7. Zawartość katalogu `deploy/`

| Plik | Rola |
| --- | --- |
| `Dockerfile.backend` | Python 3.12 slim, zależności z `pyproject.toml`, uvicorn, użytkownik nie-root, healthcheck |
| `Dockerfile.frontend` | build Vite na `node:20-alpine`, serwowanie przez `nginx:alpine` |
| `nginx.conf` | SPA fallback, proxy `/api`, nagłówki bezpieczeństwa, gzip |
| `docker-compose.yml` | usługi `backend` i `frontend`, wolumen `app-data`, zmienne z `.env` |
| `.env.example` | wzór konfiguracji |

Skrypty lokalne leżą w `scripts/`:

| Plik | Rola |
| --- | --- |
| `start-local.sh` | backend w tle + frontend, czeka na `/api/health` |
| `stop-local.sh` | zatrzymuje oba procesy po PID-ach |

---

## 8. Rozwiązywanie problemów

**`BŁĄD: brak backend/.venv/bin/python`**
Nie zainstalowano zależności backendu. `make install-backend`.

**`BŁĄD: brak frontend/node_modules/.bin/vite`**
Nie zainstalowano zależności frontendu. `make install-frontend`.

**`BŁĄD: backend zakończył pracę przed odpowiedzią na /api/health`**
Skrypt wypisuje ostatnie 30 linii `.run/backend.log`. Najczęstsze przyczyny:
zajęty port (`BACKEND_PORT=9000 scripts/start-local.sh`) albo błąd importu
w module, nad którym właśnie pracujesz.

**`node: ... GLIBCXX_3.4.30 not found`**
Node wymaga czystego `LD_LIBRARY_PATH`. Skrypty robią to same
(`env -u LD_LIBRARY_PATH`). Przy ręcznym uruchomieniu:
`env -u LD_LIBRARY_PATH npm run dev`.

**`docker compose` zgłasza brak pliku `.env`**
`cp deploy/.env.example deploy/.env`.

**`port is already allocated` w dockerze**
Zmień `APP_PORT` w `deploy/.env`.

**Frontend w dockerze zwraca 502 na `/api/...`**
Backend nie wystartował. `docker compose -f deploy/docker-compose.yml logs backend`.

**`/api/audit` zwraca `[]` mimo operacji zapisu**
Moduł `audit` działa na atrapie (dziennik w pamięci procesu, ginie przy
restarcie). Ustaw `MODULE_MODE_AUDIT=real`.

---

## 9. Bezpieczeństwo wdrożenia

- Obrazy nie zawierają `.env`, `.venv`, `node_modules` ani bazy — patrz
  `.dockerignore` w katalogu głównym.
- Backend działa jako użytkownik `app` (uid 10001), nie root.
- nginx ustawia `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy` i `Content-Security-Policy`.
- `server_tokens off` — wersja nginx nie trafia do nagłówków.
- Logi aplikacji nie zawierają danych osobowych; audyt zapisuje identyfikatory
  i nazwy akcji, nie treść dokumentów.
- Aplikacja nie wysyła pism — generuje projekt odpowiedzi do akceptacji
  urzędnika (wymaganie O1).
