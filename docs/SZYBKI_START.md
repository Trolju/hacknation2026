# Szybki start

Od zera do działającej aplikacji w trzech komendach. Pełna instrukcja
z wariantami, dockerem i rozwiązywaniem problemów: `deploy/README.md`.
Konfiguracja: `docs/ENV.md`.

## Trzy komendy

```bash
make install              # zależności backendu i frontendu — raz
cp backend/.env.example backend/.env
scripts/start-local.sh
```

Skrypt uruchamia backend na `127.0.0.1:8000`, czeka aż `/api/health` odpowie,
potem startuje frontend na `127.0.0.1:5173`. Oba procesy są odczepione od
terminala, więc przeżywają jego zamknięcie.

| Co | Adres |
| --- | --- |
| Interfejs | <http://127.0.0.1:5173> |
| Dokumentacja API | <http://127.0.0.1:8000/api/docs> |
| Stan zdrowia | <http://127.0.0.1:8000/api/health> |

## Logowanie

Wybierz konto z listy, PIN `1234` dla każdego.

| Inicjały | Osoba | Rola | Komórka |
| --- | --- | --- | --- |
| `JK` | Jan Kowalski | referent | wok |
| `AN` | Anna Nowak | kierownik | wok |
| `PW` | Piotr Wiśniewski | referent | wgk |
| `MZ` | Maria Zielińska | naczelnik | waiu |
| `TL` | Tomasz Lewandowski | referent | wfin |

Bez logowania: `AUTH_ENABLED=false` w `backend/.env`. Inicjały w sprawach biorą
się wtedy z pierwszego użytkownika `fixtures/users.json`.

## Tryb pracy

Dwa niezależne przełączniki, łatwo je pomylić:

- `MODULE_MODE_*` — czy moduł liczy naprawdę (`real`), czy czyta gotowe
  odpowiedzi z `fixtures/` (`fake`).
- `LLM_PROVIDER` — czy model językowy jest wołany (`mistral`, `llamacpp`,
  `ollama`, `openai`), czy atrapowany (`fake`).

Plik wzorcowy ustawia `MODULE_MODE_DEFAULT=real` i `LLM_PROVIDER=fake`. To
znaczy: cała logika, baza i terminy działają naprawdę, a treść odpowiedzi
pochodzi z atrapy modelu. Taki układ wystarcza do przejścia całej ścieżki
i tak działają testy end-to-end.

Żeby model odpowiadał naprawdę, uzupełnij `LLM_PROVIDER` i `LLM_API_KEY` —
patrz `docs/ENV.md`. Wszystko na atrapach, bez sieci:

```bash
MODULE_MODE_DEFAULT=fake scripts/start-local.sh
```

Stan faktyczny każdego modułu widać w Ustawieniach i w `/api/health`.

## Sprawdzenie, że działa

```bash
curl -s http://127.0.0.1:8000/api/health | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5173/
```

Oczekiwane: `"status": "ok"` i `200`.

## Zatrzymanie

```bash
scripts/stop-local.sh
```

## Wariant dockerowy

```bash
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml up --build
```

Interfejs: <http://localhost:8080>. Port zmienisz przez `APP_PORT`
w `deploy/.env`. Pierwszy build trwa kilka minut.

## Demo

```bash
scripts/demo.sh
```

Czyści `backend/data/`, ustawia tryb `fake` i `DEMO_TODAY`, uruchamia oba
serwery i wypisuje listę „co pokazać”. Scenariusz przejścia przez aplikację:
`docs/DEMO.md`.

## Testy

```bash
make test        # pytest + vitest
make check       # lint + typy + testy
make build       # produkcyjny build frontendu
```

## Gdy coś nie działa

| Objaw | Przyczyna i naprawa |
| --- | --- |
| `brak backend/.venv/bin/python` | `make install-backend` |
| `brak frontend/node_modules/.bin/vite` | `make install-frontend` |
| `backend zakończył pracę przed /api/health` | zajęty port albo błąd importu; ostatnie 30 linii jest w `.run/backend.log`, inny port: `BACKEND_PORT=9000 scripts/start-local.sh` |
| `node: GLIBCXX_3.4.30 not found` | Node wymaga czystego `LD_LIBRARY_PATH`; skrypty robią to same, ręcznie: `env -u LD_LIBRARY_PATH npm run dev` |
| `docker compose` zgłasza brak `.env` | `cp deploy/.env.example deploy/.env` |
| `port is already allocated` | zmień `APP_PORT` w `deploy/.env` |
| frontend w dockerze zwraca 502 | backend nie wstał: `docker compose -f deploy/docker-compose.yml logs backend` |
| `/api/audit` zwraca `[]` mimo zapisów | moduł `audit` na atrapie; `MODULE_MODE_AUDIT=real` |

## Co dalej

- `docs/NARZEDZIA.md` — spis bibliotek i narzędzi
- `docs/ENV.md` — wszystkie zmienne środowiskowe i gotowa templatka `.env`
- `docs/DEMO.md` — scenariusz pokazu krok po kroku
- `deploy/README.md` — pełna instrukcja wdrożenia
- `AGENTS.md` — zasady pracy w repozytorium
