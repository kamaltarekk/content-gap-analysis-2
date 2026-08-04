import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def temp_db(tmp_path):
    """Bind persistence to a fresh temporary SQLite database for one test.

    Yields the database URL so a test can simulate a process restart by calling
    ``session.configure(url)`` again (disposing pooled connections). Tables are created
    up front; the previous binding is restored on teardown.
    """
    from app.db import session

    original_url = str(session.engine.url)
    url = f"sqlite:///{tmp_path / 'test.db'}"
    session.configure(url)
    session.create_all()
    try:
        yield url
    finally:
        session.configure(original_url)
