from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

API_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "projects",
    "entities",
    "sources",
    "content_items",
    "evidence",
    "assessments",
    "gaps",
    "jobs",
}


def _alembic_config(url: str) -> Config:
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migrations_upgrade_and_downgrade(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'migrate.db'}"
    cfg = _alembic_config(url)

    command.upgrade(cfg, "head")
    tables_after_upgrade = set(inspect(create_engine(url)).get_table_names())
    assert EXPECTED_TABLES.issubset(tables_after_upgrade)

    command.downgrade(cfg, "base")
    tables_after_downgrade = set(inspect(create_engine(url)).get_table_names())
    assert EXPECTED_TABLES.isdisjoint(tables_after_downgrade)
