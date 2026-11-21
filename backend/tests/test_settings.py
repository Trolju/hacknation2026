"""Testy rozstrzygania trybu modułu (`MODULE_MODE_<NAZWA>`).

`MODULE_MODE_<NAZWA>` są dynamiczne, więc pydantic nie mapuje ich na pola.
Czytamy je sami — ze zmiennej środowiskowej albo z `.env`. Kolejność ma
znaczenie: zmienna wygrywa, bo tak działa cała reszta konfiguracji.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core import settings as settings_module
from app.core.settings import Settings


@pytest.fixture
def env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Podstawia tymczasowy `.env` i czyści cache odczytu."""
    path = tmp_path / ".env"
    monkeypatch.setattr(settings_module, "ENV_FILE", path)
    settings_module._env_file_values.cache_clear()
    yield path
    settings_module._env_file_values.cache_clear()


def _settings(**overrides: object) -> Settings:
    base: dict[str, object] = {"module_mode_default": "fake"}
    base.update(overrides)
    return Settings(_env_file=None, **base)  # type: ignore[arg-type]


def test_tryb_z_pliku_env_jest_respektowany(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("MODULE_MODE_INFERENCE=real\n", encoding="utf-8")
    monkeypatch.delenv("MODULE_MODE_INFERENCE", raising=False)

    assert _settings().module_mode("inference") == "real"


def test_zmienna_srodowiskowa_wygrywa_nad_plikiem(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("MODULE_MODE_INFERENCE=real\n", encoding="utf-8")
    monkeypatch.setenv("MODULE_MODE_INFERENCE", "fake")

    assert _settings().module_mode("inference") == "fake"


def test_brak_wpisu_daje_tryb_domyslny(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("MODULE_MODE_INFERENCE=real\n", encoding="utf-8")
    monkeypatch.delenv("MODULE_MODE_ARCHIVE", raising=False)

    assert _settings(module_mode_default="real").module_mode("archive") == "real"


def test_bez_pliku_env_zostaje_tryb_domyslny(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings_module, "ENV_FILE", None)
    settings_module._env_file_values.cache_clear()
    monkeypatch.delenv("MODULE_MODE_INFERENCE", raising=False)

    assert _settings().module_mode("inference") == "fake"
    settings_module._env_file_values.cache_clear()


def test_nieprawidlowa_wartosc_jest_ignorowana(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text("MODULE_MODE_INFERENCE=byle_co\n", encoding="utf-8")
    monkeypatch.delenv("MODULE_MODE_INFERENCE", raising=False)

    assert _settings().module_mode("inference") == "fake"


def test_komentarze_i_puste_linie_nie_przeszkadzaja(
    env_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file.write_text(
        "# komentarz\n\nMODULE_MODE_DRAFTING=real\n\n# MODULE_MODE_CASES=real\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MODULE_MODE_DRAFTING", raising=False)
    monkeypatch.delenv("MODULE_MODE_CASES", raising=False)

    settings = _settings()

    assert settings.module_mode("drafting") == "real"
    assert settings.module_mode("cases") == "fake"
