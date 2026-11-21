"""Porty — interfejsy modułów. Własność WS0, zamrożone.

Każdy port ma dwa adaptery: `fake` (fixtures, deterministyczny) i `real`
(implementacja produkcyjna w `modules/<x>/`). Wybór przez `MODULE_MODE_<X>`.
"""

from app.ports.anonymize import AnonymizerPort
from app.ports.archive import ArchiveSearchPort
from app.ports.audit import AuditPort
from app.ports.cases import CaseRepositoryPort
from app.ports.documents import DocumentParserPort, DocumentStorePort
from app.ports.drafting import DraftingPort
from app.ports.inference import EmbeddingPort, LLMPort
from app.ports.routing import DepartmentRouterPort

__all__ = [
    "AnonymizerPort",
    "ArchiveSearchPort",
    "AuditPort",
    "CaseRepositoryPort",
    "DepartmentRouterPort",
    "DocumentParserPort",
    "DocumentStorePort",
    "DraftingPort",
    "EmbeddingPort",
    "LLMPort",
]
