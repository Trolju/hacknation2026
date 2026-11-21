"""Atrapy deterministyczne.

Każda atrapa czyta `fixtures/` i zwraca powtarzalny wynik. Używane w testach
i w trybie `MODULE_MODE_*=fake`, żeby aplikacja działała od pierwszej minuty.
"""

from app.adapters.fakes.anonymize import FakeAnonymizer
from app.adapters.fakes.archive import FakeArchiveSearch
from app.adapters.fakes.audit import FakeAuditLog
from app.adapters.fakes.cases import FakeCaseRepository
from app.adapters.fakes.documents import FakeDocumentParser, FakeDocumentStore
from app.adapters.fakes.drafting import FakeDrafting
from app.adapters.fakes.inference import FakeEmbedding, FakeLLM
from app.adapters.fakes.routing import FakeDepartmentRouter

__all__ = [
    "FakeAnonymizer",
    "FakeArchiveSearch",
    "FakeAuditLog",
    "FakeCaseRepository",
    "FakeDepartmentRouter",
    "FakeDocumentParser",
    "FakeDocumentStore",
    "FakeDrafting",
    "FakeEmbedding",
    "FakeLLM",
]
