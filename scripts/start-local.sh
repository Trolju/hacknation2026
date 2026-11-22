#!/usr/bin/env bash
# Uruchamia aplikację lokalnie, bez dockera: backend (uvicorn) w tle + frontend (Vite).
#
# Użycie:
#   scripts/start-local.sh                  # backend + frontend
#   scripts/start-local.sh --backend-only   # tylko API
#   scripts/start-local.sh --frontend-only  # tylko interfejs
#   scripts/start-local.sh --help
#
# Zmienne środowiskowe (wszystkie opcjonalne):
#   BACKEND_HOST=127.0.0.1   BACKEND_PORT=8000
#   FRONTEND_HOST=127.0.0.1  FRONTEND_PORT=5173
#   HEALTH_TIMEOUT=60        # ile sekund czekać na /api/health
#   RELOAD=1                 # backend z auto-przeładowaniem (wolniej startuje)
#
# Zatrzymanie: scripts/stop-local.sh
# Logi:        .run/backend.log, .run/frontend.log

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON="$BACKEND_DIR/.venv/bin/python"
VITE="$FRONTEND_DIR/node_modules/.bin/vite"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-60}"
RELOAD="${RELOAD:-0}"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"

START_BACKEND=1
START_FRONTEND=1

info() { printf '  %s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
fail() {
    printf 'BŁĄD: %s\n' "$*" >&2
    exit 1
}

usage() {
    sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-only) START_FRONTEND=0 ;;
        --frontend-only) START_BACKEND=0 ;;
        -h | --help) usage ;;
        *) fail "nieznany argument: $1 (użyj --help)" ;;
    esac
    shift
done

# ── narzędzia ────────────────────────────────────────────────────────────
command -v curl >/dev/null 2>&1 || fail "brak programu curl — jest potrzebny do sprawdzenia /api/health"

# Usługi mają przeżyć zamknięcie terminala, więc odczepiamy je od sesji.
# `setsid` zakłada nową sesję i grupę procesów; `nohup` to wariant zapasowy.
if command -v setsid >/dev/null 2>&1; then
    DETACH=(setsid)
else
    DETACH=(nohup)
fi

pid_alive() {
    local pid_file="$1"
    [[ -f "$pid_file" ]] || return 1
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    [[ -n "$pid" ]] || return 1
    kill -0 "$pid" 2>/dev/null
}

# ── backend ──────────────────────────────────────────────────────────────
start_backend() {
    step "Backend (FastAPI + uvicorn)"

    [[ -x "$PYTHON" ]] || fail "brak $PYTHON — uruchom najpierw: make install-backend"

    if pid_alive "$BACKEND_PID_FILE"; then
        info "już działa (PID $(cat "$BACKEND_PID_FILE")) — pomijam start"
        return 0
    fi

    local uvicorn_args=(app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT")
    if [[ "$RELOAD" == "1" ]]; then
        uvicorn_args+=(--reload)
    fi

    info "startuję: uvicorn ${uvicorn_args[*]}"
    (
        cd "$BACKEND_DIR" && exec "${DETACH[@]}" "$PYTHON" -m uvicorn "${uvicorn_args[@]}"
    ) >"$BACKEND_LOG" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"

    local health_url="http://$BACKEND_HOST:$BACKEND_PORT/api/health"
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    while ((SECONDS < deadline)); do
        if curl -fsS --max-time 2 "$health_url" >/dev/null 2>&1; then
            info "gotowe: $health_url"
            info "dokumentacja API: http://$BACKEND_HOST:$BACKEND_PORT/api/docs"
            return 0
        fi
        if ! pid_alive "$BACKEND_PID_FILE"; then
            printf '\n--- %s ---\n' "$BACKEND_LOG" >&2
            tail -n 30 "$BACKEND_LOG" >&2 || true
            fail "backend zakończył pracę przed odpowiedzią na /api/health"
        fi
        sleep 0.3
    done

    printf '\n--- %s ---\n' "$BACKEND_LOG" >&2
    tail -n 30 "$BACKEND_LOG" >&2 || true
    fail "backend nie odpowiedział na /api/health w ${HEALTH_TIMEOUT}s"
}

# ── frontend ─────────────────────────────────────────────────────────────
start_frontend() {
    step "Frontend (Vite)"

    [[ -x "$VITE" ]] || fail "brak $VITE — uruchom najpierw: make install-frontend"

    if pid_alive "$FRONTEND_PID_FILE"; then
        info "już działa (PID $(cat "$FRONTEND_PID_FILE")) — pomijam start"
        return 0
    fi

    # Node w tym środowisku wymaga czystego LD_LIBRARY_PATH.
    info "startuję: vite --host $FRONTEND_HOST --port $FRONTEND_PORT"
    (
        cd "$FRONTEND_DIR" && exec "${DETACH[@]}" env -u LD_LIBRARY_PATH "$VITE" \
            --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" --strictPort
    ) >"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"

    local url="http://$FRONTEND_HOST:$FRONTEND_PORT/"
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    while ((SECONDS < deadline)); do
        if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
            info "gotowe: $url"
            return 0
        fi
        if ! pid_alive "$FRONTEND_PID_FILE"; then
            printf '\n--- %s ---\n' "$FRONTEND_LOG" >&2
            tail -n 30 "$FRONTEND_LOG" >&2 || true
            fail "frontend zakończył pracę przed odpowiedzią na $url"
        fi
        sleep 0.3
    done

    printf '\n--- %s ---\n' "$FRONTEND_LOG" >&2
    tail -n 30 "$FRONTEND_LOG" >&2 || true
    fail "frontend nie odpowiedział na $url w ${HEALTH_TIMEOUT}s"
}

# ── main ─────────────────────────────────────────────────────────────────
mkdir -p "$RUN_DIR"

printf 'Capricorn — uruchomienie lokalne\n'
printf 'katalog projektu: %s\n' "$ROOT_DIR"

if [[ "$START_BACKEND" == "1" ]]; then
    start_backend
fi
if [[ "$START_FRONTEND" == "1" ]]; then
    start_frontend
fi

step "Podsumowanie"
if [[ "$START_BACKEND" == "1" ]]; then
    info "API:      http://$BACKEND_HOST:$BACKEND_PORT/api"
    info "health:   http://$BACKEND_HOST:$BACKEND_PORT/api/health"
    info "log:      $BACKEND_LOG"
fi
if [[ "$START_FRONTEND" == "1" ]]; then
    info "interfejs: http://$FRONTEND_HOST:$FRONTEND_PORT"
    info "log:       $FRONTEND_LOG"
fi
info "zatrzymanie: scripts/stop-local.sh"
