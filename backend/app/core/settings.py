"""Konfiguracja aplikacji.

Wszystkie ustawienia przez zmienne środowiskowe lub plik `.env`.
Tryb modułu: `MODULE_MODE_<NAZWA>=fake|real`, domyślnie `MODULE_MODE_DEFAULT`.
"""

from __future__ import annotations

import os
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "fixtures"

#: Plik konfiguracji czytany przez pydantic-settings. Ścieżka względna do
#: katalogu uruchomienia — `start-local.sh` wchodzi do `backend/`.
#: Pusty `ENV_FILE` wyłącza czytanie pliku; tak robią testy, żeby nie zależeć
#: od lokalnego `.env` dewelopera (klucze API, wybrane tryby modułów).
_ENV_FILE_NAME = os.getenv("ENV_FILE", ".env")
ENV_FILE: Path | None = Path(_ENV_FILE_NAME) if _ENV_FILE_NAME else None


@lru_cache
def _env_file_values() -> dict[str, str]:
    """Wartości z `.env` jako słownik.

    Pydantic wczytuje `.env` do zadeklarowanych pól, ale `MODULE_MODE_<NAZWA>`
    są dynamiczne — nie da się ich zadeklarować z góry. Bez tego urzędnik
    wpisywał `MODULE_MODE_INFERENCE=real` do `.env` i nic się nie działo,
    bo `module_mode()` patrzył wyłącznie na zmienne środowiskowe.
    """
    if ENV_FILE is None or not ENV_FILE.exists():
        return {}
    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

ModuleMode = Literal["fake", "real"]

MODULES = (
    "cases",
    "ingest",
    "archive",
    "routing",
    "drafting",
    "anonymize",
    "inference",
    "audit",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Inteligentny asystent urzędnika"
    version: str = "0.1.0"

    # ── dane ──
    database_url: str = "sqlite:///./data/app.db"
    fixtures_dir: Path = FIXTURES_DIR

    # ── demo ──
    # Kotwica "dziś" dla fixtures. None = prawdziwa data systemowa.
    demo_today: date | None = date(2026, 3, 16)
    default_response_days: int = 14

    # ── tryb offline (T1) ──
    offline: bool = False

    # ── moduły ──
    module_mode_default: ModuleMode = "fake"

    # ── inference ──
    llm_provider: Literal["fake", "openai", "mistral", "llamacpp", "ollama"] = "fake"
    llm_model: str = "Bielik-11B-v2.3-Instruct"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = ""
    llm_timeout_s: float = 60.0
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.2

    embedding_provider: Literal["fake", "local", "openai"] = "fake"
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 384

    # ── upload ──
    max_upload_bytes: int = 10 * 1024 * 1024

    # ── CORS ──
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # ── uwierzytelnianie ──
    #: Klucz do podpisywania tokenów sesji. Pusty = losowy przy starcie, więc
    #: po restarcie wszyscy muszą zalogować się ponownie. W demo wygodniej
    #: wpisać stały klucz w `.env`.
    auth_secret: str = ""
    auth_session_hours: int = 8
    #: Wyłącznik — testy i pokazy bez logowania działają z `AUTH_ENABLED=false`.
    auth_enabled: bool = True

    def module_mode(self, name: str) -> ModuleMode:
        key = f"MODULE_MODE_{name.upper()}"
        # Zmienna środowiskowa wygrywa nad plikiem — tak samo jak w pydantic.
        raw = os.getenv(key) or _env_file_values().get(key)
        if raw in ("fake", "real"):
            return raw  # type: ignore[return-value]
        return self.module_mode_default

    def module_modes(self) -> dict[str, ModuleMode]:
        return {name: self.module_mode(name) for name in MODULES}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
