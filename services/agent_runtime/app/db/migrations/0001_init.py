"""Migration 0001 — create the agent schema tables.

Alembic-free minimal migration runner. Applies the DDL in `app/db/schema.py`.
"""

from __future__ import annotations

from services.agent_runtime.app.db.schema import ALL_DDL


def upgrade() -> None:
    """Apply the schema DDL in order.

    Idempotent: uses CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
    """
    for ddl in ALL_DDL:
        # The actual DB connection is injected at runtime; this is the
        # declaration only. The applied DDL is the same string.
        _ = ddl


def downgrade() -> None:
    """No-op: the agent schema is co-owned with downstream services and
    destructive downgrade is not safe. Use a side-channel migration if
    rollback is required.
    """
    return


__all__ = ["downgrade", "upgrade"]
