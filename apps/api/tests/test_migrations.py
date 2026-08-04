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


def test_migration_schema_matches_orm(tmp_path) -> None:
    """The migrated schema must match the ORM column-for-column.

    Guards against drift between the hand-written baseline and app.db.models — a
    mismatch would let the app expect a column Alembic never created.
    """
    from app.db.base import Base
    import app.db.models  # noqa: F401  (register tables on the metadata)

    url = f"sqlite:///{tmp_path / 'parity.db'}"
    command.upgrade(_alembic_config(url), "head")
    inspector = inspect(create_engine(url))

    for table_name, table in Base.metadata.tables.items():
        migrated_columns = {c["name"] for c in inspector.get_columns(table_name)}
        orm_columns = {c.name for c in table.columns}
        assert migrated_columns == orm_columns, (
            f"{table_name}: migration/ORM column mismatch "
            f"(missing={orm_columns - migrated_columns}, extra={migrated_columns - orm_columns})"
        )
