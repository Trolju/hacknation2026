#!/usr/bin/env bash
# Zatrzymuje aplikację uruchomioną przez scripts/start-local.sh.
#
# Użycie:
#   scripts/stop-local.sh            # backend + frontend
#   scripts/stop-local.sh --backend-only
#   scripts/stop-local.sh --frontend-only
#   scripts/stop-local.sh --help

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

STOP_BACKEND=1
STOP_FRONTEND=1

info() { printf '  %s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
fail() {
    printf 'BŁĄD: %s\n' "$*" >&2
    exit 1
}

usage() {
    sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend-only) STOP_FRONTEND=0 ;;
        --frontend-only) STOP_BACKEND=0 ;;
        -h | --help) usage ;;
        *) fail "nieznany argument: $1 (użyj --help)" ;;
    esac
    shift
done

stop_one() {
    local name="$1"
    local pid_file="$2"

    if [[ ! -f "$pid_file" ]]; then
        info "$name: nie był uruchomiony (brak pliku PID)"
        return 0
    fi

    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
        info "$name: proces ${pid:-?} już nie działa — usuwam plik PID"
        rm -f "$pid_file"
        return 0
    fi

    # Najpierw dzieci (esbuild, reloader uvicorna), potem proces główny.
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true

    local waited=0
    while kill -0 "$pid" 2>/dev/null && ((waited < 50)); do
        sleep 0.1
        waited=$((waited + 1))
    done

    if kill -0 "$pid" 2>/dev/null; then
        info "$name: nie zatrzymał się w 5 s — wysyłam SIGKILL"
        pkill -KILL -P "$pid" 2>/dev/null || true
        kill -KILL "$pid" 2>/dev/null || true
    fi

    rm -f "$pid_file"
    info "$name: zatrzymany (PID $pid)"
}

printf 'Inteligentny asystent urzędnika — zatrzymanie\n'

if [[ "$STOP_BACKEND" == "1" ]]; then
    step "Backend"
    stop_one "backend" "$BACKEND_PID_FILE"
fi
if [[ "$STOP_FRONTEND" == "1" ]]; then
    step "Frontend"
    stop_one "frontend" "$FRONTEND_PID_FILE"
fi

step "Gotowe"
