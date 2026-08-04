from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

# Register ORM models on the shared metadata (import for side effects).
import app.db.models  # noqa: E402,F401


def _connect_args(url: str) -> dict:
    # SQLite is used by the local MVP and by tests; background collection/analysis
    # jobs run in worker threads, so cross-thread use of the connection is required.
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _make_engine(url: str) -> Engine:
    return create_engine(url, connect_args=_connect_args(url), future=True)


engine: Engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def configure(url: str) -> None:
    """Rebind the engine/session to a new database URL.

    Used by tests to point persistence at a temporary database and to simulate a
    process restart by disposing existing connections.
    """
    global engine
    engine.dispose()
    engine = _make_engine(url)
    SessionLocal.configure(bind=engine)


def create_all() -> None:
    """Create all tables. Dev/local convenience; controlled environments use Alembic."""
    Base.metadata.create_all(bind=engine)


def new_session() -> Session:
    return SessionLocal()
