# Inteligentny asystent urzędnika — zadania deweloperskie.
# Node wymaga czystego LD_LIBRARY_PATH w tym środowisku.

SHELL := /bin/bash
PY := backend/.venv/bin/python
NODE := env -u LD_LIBRARY_PATH

.PHONY: help install install-backend install-frontend dev backend frontend \
        test test-backend test-frontend lint typecheck check build clean

help:
	@echo "make install     — instaluje zależności backendu i frontendu"
	@echo "make dev         — przypomina, jak uruchomić oba serwery (dwa terminale)"
	@echo "make backend     — tylko backend (http://127.0.0.1:8000)"
	@echo "make frontend    — tylko frontend (http://127.0.0.1:5173)"
	@echo "make check       — lint + typecheck + testy"
	@echo "make build       — buduje frontend do frontend/dist"

install: install-backend install-frontend

install-backend:
	cd backend && uv venv --python 3.12 .venv 2>/dev/null || true
	cd backend && uv pip install -e ".[dev,documents]"

install-frontend:
	cd frontend && $(NODE) npm install --no-audit --no-fund

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && $(NODE) npm run dev

dev:
	@echo "Uruchom w dwóch terminalach: make backend oraz make frontend"

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/python -m pytest -q

test-frontend:
	cd frontend && $(NODE) npm run test

lint:
	cd backend && .venv/bin/ruff check app tests
	cd frontend && $(NODE) npm run lint

typecheck:
	cd backend && .venv/bin/mypy app
	cd frontend && $(NODE) ./node_modules/.bin/tsc -p tsconfig.app.json --noEmit

check: lint typecheck test

build:
	cd frontend && $(NODE) npm run build

clean:
	rm -rf backend/.venv frontend/node_modules frontend/dist backend/.pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
