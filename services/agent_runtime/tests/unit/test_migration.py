"""Unit tests for the migration runner (app/db/migrations/0001_init.py).

Covers BUG J:
- upgrade() actually executes every DDL string in ALL_DDL.
- ALL_DDL is prefixed by the CREATE SCHEMA statement.
- ALL_DDL has exactly 4 entries (schema + 3 tables).
"""

from __future__ import annotations

import importlib
from typing import Any

from services.agent_runtime.app.db.schema import ALL_DDL


def _load_migration() -> Any:
    # The module name starts with a digit, so it cannot be a plain import.
    return importlib.import_module("services.agent_runtime.app.db.migrations.0001_init")


def test_migration_upgrade_executes_all_ddl() -> None:
    """BUG J: upgrade(execute) must invoke execute for every DDL string."""
    migration = _load_migration()
    calls: list[str] = []
    migration.upgrade(execute=calls.append)
    assert len(calls) == len(ALL_DDL)
    assert "CREATE SCHEMA IF NOT EXISTS agent" in calls[0]


def test_schema_all_ddl_starts_with_create_schema() -> None:
    """BUG J: ALL_DDL[0] creates the agent schema before any table DDL."""
    assert "CREATE SCHEMA IF NOT EXISTS agent" in ALL_DDL[0]


def test_schema_ddl_count() -> None:
    """BUG J: ALL_DDL = CREATE SCHEMA + 3 tables = 4 entries."""
    assert len(ALL_DDL) == 4
