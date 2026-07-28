"""SessionManager interface for auth-svc.

See DESIGN.md for the full design rationale, the TTL semantics, the
concurrency model, and the audit-event contract.
"""

from __future__ import annotations

import abc
import logging
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

IDLE_TTL: timedelta = timedelta(hours=8)
ABSOLUTE_TTL: timedelta = timedelta(days=30)
MAX_INITIAL_TTL: timedelta = IDLE_TTL


class Session(BaseModel):
    session_id: UUID
    user_id: UUID
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"frozen": False}


def _default_clock() -> datetime:
    return datetime.now(UTC)


def _default_audit_sink(event_code: str, payload: dict[str, Any]) -> None:
    logging.getLogger("auth_svc.audit").info("auth.audit event=%s payload=%s", event_code, payload)


class SessionManager(abc.ABC):
    def __init__(self, *, clock=None, audit_sink=None, idle_ttl=IDLE_TTL, absolute_ttl=ABSOLUTE_TTL):
        self._clock = clock or _default_clock
        self._audit_sink = audit_sink or _default_audit_sink
        self._idle_ttl = idle_ttl
        self._absolute_ttl = absolute_ttl

    @abc.abstractmethod
    def create_session(self, user_id, *, ttl=None, metadata=None): ...
    @abc.abstractmethod
    def get_session(self, session_id): ...
    @abc.abstractmethod
    def refresh_session(self, session_id): ...
    @abc.abstractmethod
    def revoke_session(self, session_id): ...
    @abc.abstractmethod
    def revoke_all_for_user(self, user_id): ...

    def _now(self): return self._clock()
    def _emit(self, event_code, payload): self._audit_sink(event_code, payload)
    def _is_idle_expired(self, session): return (self._now() - session.last_used_at) > self._idle_ttl
    def _is_max_expired(self, session): return self._now() >= session.expires_at
    def _new_session_id(self): return uuid.uuid4()


class InMemorySessionManager(SessionManager):
    def __init__(self, *, clock=None, audit_sink=None, idle_ttl=IDLE_TTL, absolute_ttl=ABSOLUTE_TTL):
        super().__init__(clock=clock, audit_sink=audit_sink, idle_ttl=idle_ttl, absolute_ttl=absolute_ttl)
        self._sessions = {}
        self._by_user = {}
        self._lock = threading.Lock()

    def create_session(self, user_id, *, ttl=None, metadata=None):
        if user_id is None:
            raise ValueError("user_id is required")
        if ttl is not None:
            if ttl <= timedelta(0):
                raise ValueError("ttl must be > 0")
            if ttl > self._idle_ttl:
                raise ValueError(f"ttl must be <= {self._idle_ttl}")
        now = self._now()
        session_id = self._new_session_id()
        session = Session(session_id=session_id, user_id=user_id, created_at=now, expires_at=now + self._absolute_ttl, last_used_at=now, metadata=dict(metadata) if metadata else {})
        with self._lock:
            self._sessions[session_id] = session
            self._by_user.setdefault(user_id, set()).add(session_id)
        self._emit("session.created", {"session_id": str(session_id), "user_id": str(user_id)})
        return session

    def get_session(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._is_idle_expired(session) or self._is_max_expired(session):
                self._sessions.pop(session_id, None)
                user_sids = self._by_user.get(session.user_id)
                if user_sids is not None:
                    user_sids.discard(session_id)
                    if not user_sids:
                        self._by_user.pop(session.user_id, None)
                return None
            now = self._now()
            updated = session.model_copy(update={"last_used_at": now})
            self._sessions[session_id] = updated
            return updated

    def refresh_session(self, session_id):
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._is_idle_expired(session) or self._is_max_expired(session):
                self._sessions.pop(session_id, None)
                user_sids = self._by_user.get(session.user_id)
                if user_sids is not None:
                    user_sids.discard(session_id)
                    if not user_sids:
                        self._by_user.pop(session.user_id, None)
                return None
            now = self._now()
            updated = session.model_copy(update={"last_used_at": now})
            self._sessions[session_id] = updated
        self._emit("session.refreshed", {"session_id": str(session_id), "user_id": str(session.user_id)})
        return updated

    def revoke_session(self, session_id):
        with self._lock:
            session = self._sessions.pop(session_id, None)
            if session is None:
                return False
            user_sids = self._by_user.get(session.user_id)
            if user_sids is not None:
                user_sids.discard(session_id)
                if not user_sids:
                    self._by_user.pop(session.user_id, None)
        self._emit("session.revoked", {"session_id": str(session_id), "user_id": str(session.user_id)})
        return True

    def revoke_all_for_user(self, user_id):
        with self._lock:
            sids = self._by_user.pop(user_id, set())
            for sid in sids:
                self._sessions.pop(sid, None)
            count = len(sids)
        if count > 0:
            self._emit("session.revoked_all_for_user", {"user_id": str(user_id), "count": count})
        return count
