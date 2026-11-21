#!/usr/bin/env bash
# Przygotowuje i uruchamia środowisko demonstracyjne.
#
# Co robi:
#   1. zatrzymuje poprzednio uruchomioną aplikację,
#   2. czyści `backend/data/` (baza i uploady), żeby demo było powtarzalne,
#   3. ustawia `MODULE_MODE_DEFAULT=fake` i `DEMO_TODAY=2026-03-16`,
#   4. uruchamia backend i frontend przez `scripts/start-local.sh`,
#   5. wypisuje adresy i listę „co pokazać”.
#
# Użycie:
#   scripts/demo.sh                  # pełne demo: backend + frontend
#   scripts/demo.sh --backend-only   # tylko API (frontend uruchom osobno)
#   scripts/demo.sh --frontend-only  # tylko interfejs
#   scripts/demo.sh --no-reset       # nie czyść danych (kontynuacja demo)
#   scripts/demo.sh --help
#
# Zatrzymanie: scripts/stop-local.sh
# Scenariusz przejścia przez aplikację: docs/DEMO.md

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
DATA_DIR="$BACKEND_DIR/data"
RUN_DIR="$ROOT_DIR/.run"
PYTHON="$BACKEND_DIR/.venv/bin/python"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Kotwica „dziś” dla danych demonstracyjnych — dzięki niej terminy w kalendarzu
# mają sens (16 marca 2026: jeden wniosek po terminie, jeden z terminem na dziś,
# dwa w najbliższych dniach).
DEMO_TODAY="${DEMO_TODAY:-2026-03-16}"

RESET=1
START_ARGS=()

info() { printf '  %s\n' "$*"; }
step() { printf '\n==> %s\n' "$*"; }
fail() {
    printf 'BŁĄD: %s\n' "$*" >&2
    exit 1
}

usage() {
    sed -n '2,19p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-reset) RESET=0 ;;
        --backend-only | --frontend-only) START_ARGS+=("$1") ;;
        -h | --help) usage ;;
        *) fail "nieznany argument: $1 (użyj --help)" ;;
    esac
    shift
done

[[ -x "$PYTHON" ]] || fail "brak $PYTHON — uruchom najpierw: make install-backend"

printf 'Inteligentny asystent urzędnika — środowisko demonstracyjne\n'
printf 'katalog projektu: %s\n' "$ROOT_DIR"

# ── 1. zatrzymanie poprzedniego uruchomienia ────────────────────────────────
step "Zatrzymanie poprzedniego uruchomienia"
"$ROOT_DIR/scripts/stop-local.sh" >/dev/null 2>&1 || true
info "gotowe (jeśli coś działało, jest już zatrzymane)"

# ── 2. czyszczenie danych ───────────────────────────────────────────────────
step "Czyszczenie danych demo"
if [[ "$RESET" == "1" ]]; then
    rm -rf "$DATA_DIR"
    rm -f "$RUN_DIR/backend.log" "$RUN_DIR/frontend.log"
    info "usunięto $DATA_DIR (baza SQLite i uploady)"
    info "usunięto logi z $RUN_DIR"
else
    info "pominięto (--no-reset) — demo startuje na danych z poprzedniego przebiegu"
fi

# ── 3. tryb pracy ───────────────────────────────────────────────────────────
step "Tryb pracy"
# Demo działa bez modeli i bez sieci: wszystkie moduły na atrapach z fixtures/.
# Zmienne MODULE_MODE_<NAZWA> z powłoki mogłyby to popsuć, więc je zdejmujemy.
for module in CASES INGEST ARCHIVE ROUTING DRAFTING ANONYMIZE INFERENCE AUDIT; do
    unset "MODULE_MODE_$module"
done
export MODULE_MODE_DEFAULT=fake
export DEMO_TODAY
export OFFLINE=false
# Adresy i porty muszą przejść do `start-local.sh`, inaczej uruchomi się na
# domyślnych 8000/5173, a podsumowanie pokaże inne numery.
export BACKEND_HOST BACKEND_PORT FRONTEND_HOST FRONTEND_PORT
info "MODULE_MODE_DEFAULT=fake (wszystkie moduły na danych z fixtures/)"
info "DEMO_TODAY=$DEMO_TODAY"

# ── 4. uruchomienie ─────────────────────────────────────────────────────────
"$ROOT_DIR/scripts/start-local.sh" ${START_ARGS[@]+"${START_ARGS[@]}"}

# ── 5. podsumowanie ─────────────────────────────────────────────────────────
API_URL="http://$BACKEND_HOST:$BACKEND_PORT/api"
APP_URL="http://$FRONTEND_HOST:$FRONTEND_PORT"

step "Adresy"
info "interfejs:  $APP_URL"
info "API:        $API_URL"
info "dokumentacja API: $API_URL/docs"
info "health:     $API_URL/health"

if [[ ${#START_ARGS[@]} -eq 0 || " ${START_ARGS[*]} " != *" --frontend-only "* ]]; then
    cases_count="$(curl -fsS --max-time 5 "$API_URL/cases" 2>/dev/null |
        grep -o '"case_number"' | wc -l | tr -d ' ')" || cases_count="?"
    info "w kalendarzu: ${cases_count} wniosków (dane z fixtures/cases/cases.json)"
fi

step "Co pokazać (szczegóły krok po kroku: docs/DEMO.md)"
info "1. Pulpit — zaległości, terminy na dziś i na jutro."
info "2. Kalendarz — wniosek UDIP.1435.1.2026 po terminie, filtry i widok miesiąca."
info "3. Dokumenty — wgraj fixtures/documents/wniosek-01-wynagrodzenia.pdf (rodzaj: wniosek)."
info "4. Archiwum — wpisz „wynagrodzenia pracowników”, pokaż sprawę a0001."
info "5. Routing — sprawa UDIP.1435.1.2026, komórka wok, wygeneruj zapytanie."
info "6. Generator odpowiedzi — projekt z cytowaniami, korekta, eksport DOCX/PDF."
info "7. Anonimizacja — wklej tekst z nazwiskiem i PESEL-em, pokaż usunięcia."
info "8. Ustawienia — tryby modułów i stan warstwy modeli."

step "Zatrzymanie"
info "scripts/stop-local.sh"
info "logi: $RUN_DIR/backend.log, $RUN_DIR/frontend.log"
