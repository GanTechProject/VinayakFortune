"""SessionManager interface for auth-svc.

This file ships the abstract base class (the contract) and the Session
Pydantic model. The InMemorySessionManager concrete class is a
follow-up that the implementer writes to make the RED test spec pass.

See DESIGN.md for the full design rationale, the TTL semantics, the
concurrency model, and the audit-event contract.

This module deliberately ships the ABC ONLY (no concrete class). The
import path is stable; the implementer's job is to add
`InMemorySessionManager` to this module without changing the public
API of `SessionManager`.
"""

from __future__ import annotations

import abc
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Constants — TTL ceilings from Document 02 §5.5
# ---------------------------------------------------------------------------

IDLE_TTL: timedelta = timedelta(hours=8)        # 8h sliding window
ABSOLUTE_TTL: timedelta = timedelta(days=30)    # 30d absolute ceiling
MAX_INITIAL_TTL: timedelta = IDLE_TTL           # the `ttl` parameter to create_session is capped at 8h


# ---------------------------------------------------------------------------
# Session data model
# ---------------------------------------------------------------------------


class Session(BaseModel):
    """An authenticated user session, identified by an opaque session_id.

    See DESIGN.md §3 for invariants and lifecycle.
    """

    session_id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}  # the manager mutates last_used_at on get/refresh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_clock() -> datetime:
    """Return the current UTC time.

    The default clock. Tests inject a fake clock to make TTL behavior
    deterministic. The clock must return a *tz-aware* UTC datetime so
    arithmetic against `created_at` (also tz-aware) does not raise.
    """
    return datetime.now(timezone.utc)


def _default_audit_sink(event_code: str, payload: dict[str, Any]) -> None:
    """Default audit sink: log at INFO. Production swaps this for a durable sink."""
    logging.getLogger("auth_svc.audit").info(
        "auth.audit event=%s payload=%s", event_code, payload
    )


# ---------------------------------------------------------------------------
# SessionManager — the contract every backend must satisfy
# ---------------------------------------------------------------------------


class SessionManager(abc.ABC):
    """The contract every session-manager backend must satisfy.

    All methods are thread-safe. The in-memory backend uses a single
    `threading.Lock`; the Redis backend (out of scope) will use a
    per-session Lua script. Both backends must produce the same
    observable behavior under the RED test spec in DESIGN.md §10.

    The interface is sync. The eventual FastAPI service is async; the
    HTTP layer wraps calls in `asyncio.to_thread` if the backend is
    sync. See DESIGN.md §12.1 for the open question on async vs sync.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        audit_sink: Callable[[str, dict[str, Any]], None] | None = None,
        idle_ttl: timedelta = IDLE_TTL,
        absolute_ttl: timedelta = ABSOLUTE_TTL,
    ) -> None:
        self._clock = clock or _default_clock
        self._audit_sink = audit_sink or _default_audit_sink
        self._idle_ttl = idle_ttl
        self._absolute_ttl = absolute_ttl

    # ----- lifecycle --------------------------------------------------------

    @abc.abstractmethod
    def create_session(
        self,
        user_id: UUID,
        *,
        ttl: timedelta | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Session:
        """Create a new session for `user_id`.

        See DESIGN.md §5 for the full contract. Raises ValueError on
        invalid inputs (None user_id, ttl <= 0, ttl > 8h).
        """

    @abc.abstractmethod
    def get_session(self, session_id: UUID) -> Session | None:
        """Return the session if it exists and is not expired.

        Updates last_used_at on a hit. Returns None on miss or any
        kind of expiry. Does NOT raise on expiry.
        """

    @abc.abstractmethod
    def refresh_session(self, session_id: UUID) -> Session | None:
        """Extend the idle window on an existing session.

        Updates last_used_at. Returns the refreshed session, or None
        if missing or expired. Does NOT extend expires_at.
        """

    @abc.abstractmethod
    def revoke_session(self, session_id: UUID) -> bool:
        """Revoke a single session. Idempotent. Returns True on hit, False on miss."""

    @abc.abstractmethod
    def revoke_all_for_user(self, user_id: UUID) -> int:
        """Revoke every active session for `user_id`. Returns the count revoked."""

    # ----- helpers exposed for concrete subclasses -------------------------

    def _now(self) -> datetime:
        return self._clock()

    def _emit(self, event_code: str, payload: dict[str, Any]) -> None:
        """Emit an audit event. Concrete subclasses call this after mutation."""
        self._audit_sink(event_code, payload)

    def _is_idle_expired(self, session: Session) -> bool:
        return (self._now() - session.last_used_at) > self._idle_ttl

    def _is_max_expired(self, session: Session) -> bool:
        return self._now() >= session.expires_at

    def _new_session_id(self) -> UUID:
        return uuid.uuid4()
