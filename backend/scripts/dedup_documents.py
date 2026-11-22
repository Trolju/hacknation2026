"""Usuwa duplikaty dokumentów wgrane przed deduplikacją po SHA-256.

Deduplikacja działa od commita, który dodał `content_hash`, ale dokumenty
wgrane wcześniej leżą w bazie podwójnie — ten sam plik pod tą samą nazwą
albo pod dwiema różnymi. Skrypt zostawia najstarszy wpis z danej treści
i usuwa pozostałe razem z ich fragmentami i plikami na dysku.

Wpisy bez `content_hash` dostają skrót policzony z pliku na dysku, a gdy
pliku już nie ma — z rozpoznanego tekstu. Bez tego kroku starych wpisów
nie dałoby się pogrupować.

Uruchomienie:

    cd backend && .venv/bin/python scripts/dedup_documents.py --dry-run
    cd backend && .venv/bin/python scripts/dedup_documents.py

Skrypt jest idempotentny: drugie uruchomienie nie znajduje już nic do
usunięcia.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.modules.ingest.models import DocumentChunkRow, DocumentRow  # noqa: E402


def _hash_of(row: DocumentRow) -> str:
    """Skrót treści wpisu: z pliku, a gdy pliku brak — z rozpoznanego tekstu."""
    if row.storage_path:
        path = Path(row.storage_path)
        if path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()
    return hashlib.sha256((row.text or "").encode("utf-8")).hexdigest()


def _backfill(session: Session) -> int:
    """Uzupełnia `content_hash` w starych wpisach; zwraca liczbę uzupełnień."""
    rows = session.scalars(
        select(DocumentRow).where(DocumentRow.content_hash.is_(None))
    ).all()
    for row in rows:
        row.content_hash = _hash_of(row)
    return len(rows)


def _duplicates(rows: list[DocumentRow]) -> list[DocumentRow]:
    """Wpisy do usunięcia — z każdej grupy zostaje najstarszy."""
    groups: dict[tuple[str, str | None, str | None], list[DocumentRow]] = defaultdict(list)
    for row in rows:
        groups[(row.kind, row.case_id, row.content_hash)].append(row)

    doomed: list[DocumentRow] = []
    for group in groups.values():
        if len(group) < 2:
            continue
        group.sort(key=lambda row: (row.created_at, row.id))
        doomed.extend(group[1:])
    return doomed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="pokaż, co zostałoby usunięte, bez zmiany bazy",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        backfilled = _backfill(session)
        rows = session.scalars(select(DocumentRow)).all()
        doomed = _duplicates(list(rows))

        print(f"wpisów w bazie: {len(rows)}")
        print(f"uzupełniono content_hash: {backfilled}")
        print(f"duplikatów do usunięcia: {len(doomed)}")

        for row in doomed:
            print(f"  - {row.filename} ({row.kind}, {row.id})")

        if args.dry_run:
            session.rollback()
            print("\n--dry-run: baza bez zmian.")
            return 0

        for row in doomed:
            session.execute(
                delete(DocumentChunkRow).where(DocumentChunkRow.document_id == row.id)
            )
            session.delete(row)
        session.commit()

    for row in doomed:
        if row.storage_path:
            path = Path(row.storage_path)
            if path.is_file():
                path.unlink()

    print(f"\nusunięto {len(doomed)} duplikatów.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
