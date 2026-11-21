"""Ładowanie fixtures — z cache, read-only."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.settings import settings


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def cases() -> list[dict[str, Any]]:
    return _read(settings.fixtures_dir / "cases" / "cases.json")


@lru_cache
def archive() -> list[dict[str, Any]]:
    return _read(settings.fixtures_dir / "archive" / "archive.json")


@lru_cache
def departments() -> list[dict[str, Any]]:
    return _read(settings.fixtures_dir / "departments.json")


@lru_cache
def anonymization_samples() -> list[dict[str, Any]]:
    path = settings.fixtures_dir / "anonymization" / "labeled.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@lru_cache
def statute(name: str) -> str:
    return (settings.fixtures_dir / "statutes" / f"{name}.txt").read_text(encoding="utf-8")


def statute_names() -> list[str]:
    return sorted(p.stem for p in (settings.fixtures_dir / "statutes").glob("*.txt"))
