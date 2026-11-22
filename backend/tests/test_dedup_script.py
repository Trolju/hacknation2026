"""Skrypt porządkowy dla duplikatów sprzed deduplikacji po SHA-256.

P13 z raportu z testów na żywym Mistralu: deduplikacja działa dla nowych
wgrań, ale dokumenty wgrane przed commitem `5356e68` leżały w bazie
podwójnie. Skrypt zostawia najstarszy wpis z danej treści i usuwa pozostałe.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base
from app.modules.ingest.models import DocumentChunkRow, DocumentRow

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dedup_documents.py"


@pytest.fixture(scope="module")
def script() -> ModuleType:
    """Skrypt nie jest pakietem — ładujemy go po ścieżce."""
    spec = importlib.util.spec_from_file_location("dedup_documents", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["dedup_documents"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def session(tmp_path: Path) -> Session:
    engine: Engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as opened:
        yield opened


def _row(
    *,
    document_id: str,
    filename: str,
    content_hash: str | None,
    created_at: datetime,
    kind: str = "wniosek",
    case_id: str | None = None,
    storage_path: str | None = None,
    text: str = "",
) -> DocumentRow:
    return DocumentRow(
        id=document_id,
        kind=kind,
        filename=filename,
        mime="application/pdf",
        size_bytes=len(text),
        status="indexed",
        case_id=case_id,
        chunk_count=0,
        page_count=1,
        text=text,
        storage_path=storage_path,
        content_hash=content_hash,
        created_at=created_at,
    )


BASE_TIME = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


class TestDuplicates:
    def test_zostawia_najstarszy_wpis(self, script: ModuleType) -> None:
        older = _row(
            document_id="a",
            filename="wniosek.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
        )
        newer = _row(
            document_id="b",
            filename="wniosek-kopia.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME + timedelta(hours=1),
        )

        doomed = script._duplicates([older, newer])

        assert [row.id for row in doomed] == ["b"]

    def test_rozne_tresci_zostaja(self, script: ModuleType) -> None:
        first = _row(
            document_id="a",
            filename="wniosek.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
        )
        second = _row(
            document_id="b",
            filename="wniosek.pdf",
            content_hash="hash-2",
            created_at=BASE_TIME,
        )

        assert script._duplicates([first, second]) == []

    def test_rozne_sprawy_nie_sa_duplikatem(self, script: ModuleType) -> None:
        """Ten sam plik w dwóch sprawach to dwa osobne dokumenty."""
        first = _row(
            document_id="a",
            filename="wniosek.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
            case_id="case-1",
        )
        second = _row(
            document_id="b",
            filename="wniosek.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
            case_id="case-2",
        )

        assert script._duplicates([first, second]) == []

    def test_rozne_rodzaje_nie_sa_duplikatem(self, script: ModuleType) -> None:
        first = _row(
            document_id="a",
            filename="akt.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
            kind="ustawa",
        )
        second = _row(
            document_id="b",
            filename="akt.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
            kind="wniosek",
        )

        assert script._duplicates([first, second]) == []

    def test_trzy_kopie_zostawiaja_jedna(self, script: ModuleType) -> None:
        rows = [
            _row(
                document_id=name,
                filename=f"wniosek-{name}.pdf",
                content_hash="hash-1",
                created_at=BASE_TIME + timedelta(minutes=index),
            )
            for index, name in enumerate(("a", "b", "c"))
        ]

        doomed = script._duplicates(rows)

        assert [row.id for row in doomed] == ["b", "c"]


class TestBackfill:
    def test_uzupelnia_skrot_z_pliku(
        self, script: ModuleType, session: Session, tmp_path: Path
    ) -> None:
        stored = tmp_path / "wniosek.pdf"
        stored.write_bytes(b"tresc wniosku")
        session.add(
            _row(
                document_id="a",
                filename="wniosek.pdf",
                content_hash=None,
                created_at=BASE_TIME,
                storage_path=str(stored),
            )
        )
        session.commit()

        assert script._backfill(session) == 1
        session.commit()

        row = session.scalars(select(DocumentRow)).one()
        assert row.content_hash is not None
        assert len(row.content_hash) == 64

    def test_bez_pliku_liczy_z_tekstu(
        self, script: ModuleType, session: Session
    ) -> None:
        session.add(
            _row(
                document_id="a",
                filename="wniosek.pdf",
                content_hash=None,
                created_at=BASE_TIME,
                text="tresc wniosku",
            )
        )
        session.commit()

        assert script._backfill(session) == 1
        session.commit()

        row = session.scalars(select(DocumentRow)).one()
        assert row.content_hash is not None

    def test_nie_rusza_wpisow_z_skrotem(
        self, script: ModuleType, session: Session
    ) -> None:
        session.add(
            _row(
                document_id="a",
                filename="wniosek.pdf",
                content_hash="hash-1",
                created_at=BASE_TIME,
            )
        )
        session.commit()

        assert script._backfill(session) == 0


class TestCleanup:
    def test_usuwa_duplikat_wraz_z_fragmentami(
        self, script: ModuleType, session: Session
    ) -> None:
        older = _row(
            document_id="a",
            filename="wniosek.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME,
        )
        newer = _row(
            document_id="b",
            filename="wniosek-kopia.pdf",
            content_hash="hash-1",
            created_at=BASE_TIME + timedelta(hours=1),
        )
        session.add_all([older, newer])
        session.add(
            DocumentChunkRow(
                id="chunk-b",
                document_id="b",
                index=0,
                text="fragment duplikatu",
            )
        )
        session.commit()

        doomed = script._duplicates(list(session.scalars(select(DocumentRow)).all()))
        for row in doomed:
            session.execute(
                DocumentChunkRow.__table__.delete().where(
                    DocumentChunkRow.document_id == row.id
                )
            )
            session.delete(row)
        session.commit()

        remaining = session.scalars(select(DocumentRow)).all()
        assert [row.id for row in remaining] == ["a"]
        assert session.scalars(select(DocumentChunkRow)).all() == []
