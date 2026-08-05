"""Migration 0001 — create the agent schema tables.

Alembic-free minimal migration runner. Applies the DDL in `app/db/schema.py`.
"""

from __future__ import annotations

from services.agent_runtime.app.db.schema import ALL_DDL


def upgrade(execute) -> None:
    """Apply the schema DDL in order.

    execute: callable that accepts a DDL string and executes it.
    Idempotent: uses CREATE SCHEMA IF NOT EXISTS / CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
    """
    for ddl in ALL_DDL:
        execute(ddl)


def downgrade() -> None:
    """No-op: the agent schema is co-owned with downstream services and
    destructive downgrade is not safe. Use a side-channel migration if
    rollback is required.
    """
    return


__all__ = ["downgrade", "upgrade"]
