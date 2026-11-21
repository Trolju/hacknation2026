"""Kontener zależności.

Jedno miejsce, w którym wybierany jest adapter: `fake` albo `real`.
Moduły dostają zależności przez `Depends`, nigdy przez import konkretnej klasy.

Reguła: jeśli `MODULE_MODE_<NAZWA>=real`, a adapter realny nie istnieje,
kontener głośno loguje ostrzeżenie i wraca do atrapy — aplikacja nigdy nie
przestaje działać z powodu brakującego modułu.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.adapters.fakes import (
    FakeAnonymizer,
    FakeArchiveSearch,
    FakeAuditLog,
    FakeCaseRepository,
    FakeDepartmentRouter,
    FakeDocumentParser,
    FakeDocumentStore,
    FakeDrafting,
    FakeEmbedding,
    FakeLLM,
)
from app.core.settings import settings

log = structlog.get_logger(__name__)

_instances: dict[str, Any] = {}


def _real(module: str, attr: str) -> Any | None:
    """Importuje adapter realny, jeśli istnieje."""
    try:
        mod = __import__(f"app.adapters.real.{module}", fromlist=[attr])
    except ImportError:
        return None
    return getattr(mod, attr, None)


def _resolve(
    name: str, fake_factory: Any, real_attr: str, real_module: str | None = None
) -> Any:
    if name in _instances:
        return _instances[name]
    mode = settings.module_mode(name)
    instance = None
    if mode == "real":
        factory = _real(real_module or name, real_attr)
        if factory is None:
            log.warning(
                "adapter_real_missing",
                module=name,
                fallback="fake",
                expected=f"{real_module or name}.{real_attr}",
            )
        else:
            instance = factory()
    if instance is None:
        instance = fake_factory()
    _instances[name] = instance
    return instance


def reset() -> None:
    """Czyści singletony — używane w testach."""
    _instances.clear()


# ── zależności ──
def get_cases() -> FakeCaseRepository:
    return _resolve("cases", FakeCaseRepository, "SqlCaseRepository")


def get_archive() -> FakeArchiveSearch:
    return _resolve("archive", FakeArchiveSearch, "VectorArchiveSearch")


def get_routing() -> FakeDepartmentRouter:
    return _resolve("routing", FakeDepartmentRouter, "KeywordDepartmentRouter")


def get_drafting() -> FakeDrafting:
    return _resolve("drafting", FakeDrafting, "LlmDrafting")


def get_anonymizer() -> FakeAnonymizer:
    return _resolve("anonymize", FakeAnonymizer, "NerAnonymizer")


def get_llm() -> FakeLLM:
    return _resolve("inference", FakeLLM, "OpenAICompatibleLLM")


def get_embedding() -> FakeEmbedding:
    return _resolve(
        "inference_embedding", FakeEmbedding, "LocalEmbedding", real_module="inference"
    )


def get_documents() -> FakeDocumentStore:
    return _resolve(
        "ingest", FakeDocumentStore, "SqlDocumentStore", real_module="documents"
    )


def get_parser() -> FakeDocumentParser:
    return _resolve(
        "ingest_parser", FakeDocumentParser, "PdfDocxParser", real_module="documents"
    )


def get_audit() -> FakeAuditLog:
    return _resolve("audit", FakeAuditLog, "SqlAuditLog")
