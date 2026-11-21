"""Baza danych — SQLite przez SQLAlchemy 2.0.

Moduły definiują własne tabele w `modules/<x>/models.py` i importują `Base`.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.settings import settings


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite:///") and ":memory:" not in url:
        path = Path(url.removeprefix("sqlite:///"))
        path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all() -> None:
    """Tworzy tabele. Importuje modele, żeby zarejestrowały się w metadanych."""
    import importlib
    from pathlib import Path as _P

    modules_dir = _P(__file__).resolve().parents[1] / "modules"
    for models in sorted(modules_dir.glob("*/models.py")):
        importlib.import_module(f"app.modules.{models.parent.name}.models")
    Base.metadata.create_all(bind=engine)
