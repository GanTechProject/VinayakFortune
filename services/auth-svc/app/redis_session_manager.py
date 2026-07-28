"""Redis 7 SessionManager backend.

Implements the same `SessionManager` ABC as `InMemorySessionManager`, backed
by a single Redis 7 instance. Storage model, TTL semantics, and concurrency
contract are defined in `REDIS_BACKEND_DESIGN.md`. This module is the
runtime; the design doc is the spec.

Key invariants (preserved by the wrapper, enforced by the Lua scripts):

- Atomicity. Each mutating operation runs as a single EVAL/EVALSHA so the
  state transitions are not interleavable across concurrent actors.
- Clock injection. The injected `clock()` is the source of truth for
  `created_at`, `expires_at`, `last_used_at`, AND for the unix-seconds
  used to drive `EXPIREAT`. The design doc §4.1 requires this so the
  fake clock controls expiry even when Redis's own clock would disagree.
  The ONE place `time.time()` is read is in the create_session wrapper,
  to guard against Redis deleting a freshly-created key whose
  injected-clock-derived `expires_at_unix` happens to be in the past
  relative to Redis's wall clock; this is a safety guard, not a source
  of truth.
- Audit asymmetry. `get_session` never emits (per ABC); `revoke_*` emits
  only on hit; `refresh_session` emits only on hit. Audit is post-script
  (design doc §6) so the script's atomicity is independent of the sink's
  latency.

Storage layout:

- `auth_svc:session:{session_id}` — Hash (per session).
- `auth_svc:user_sessions:{user_id}` — Set (per-user session index).

The user-set TTL is recomputed to the max of its members' `expires_at_unix`
on every `create_session` so the set cannot outlive the latest session it
indexes (design doc §3.3). The Lua script `recompute_user_set_ttl_lua` is
called from the Python wrapper after `create_session_lua` returns.
"""

from __future__ import annotations

import json
import time
from datetime import timedelta
from uuid import UUID

import redis

from app.session_manager import (
    ABSOLUTE_TTL,
    IDLE_TTL,
    MAX_INITIAL_TTL,
    Session,
    SessionManager,
)

# Storage key prefix (single Redis instance can be shared in dev).
_KEY_PREFIX = "auth_svc:"
_SESSION_KEY = _KEY_PREFIX + "session:"
_USER_SET_KEY = _KEY_PREFIX + "user_sessions:"


# ---------------------------------------------------------------------------
# Lua scripts (registered via redis.Redis.register_script so SHA is cached
# after the first call; subsequent calls use EVALSHA).
# ---------------------------------------------------------------------------
#
# Each script is a single string constant. The leading comment documents the
# KEYS and ARGV contracts the script depends on. The Python wrapper is
# responsible for computing clock-derived ARGV (e.g. now_unix, expires_unix)
# from the injected clock; the Lua only does integer arithmetic and one
# round-trip (design doc §5).

# KEYS[1] = auth_svc:session:{session_id}
# KEYS[2] = auth_svc:user_sessions:{user_id}
# ARGV[1] = user_id (string)
# ARGV[2] = created_at (ISO 8601)
# ARGV[3] = expires_at (ISO 8601)
# ARGV[4] = expires_at_unix (int, injected-clock-derived; load-bearing)
# ARGV[5] = last_used_at (ISO 8601)
# ARGV[6] = last_used_at_unix (int, injected-clock-derived; load-bearing)
# ARGV[7] = metadata (JSON string)
# ARGV[8] = session_id (string, for SADD into the user-set)
# ARGV[9] = redis_now_unix (int, REAL wall clock; used only to decide whether
#           to set EXPIREAT. The injected clock is the source of truth for
#           expiry; this is just a guard against Redis deleting the key
#           immediately when fake_now + ABSOLUTE_TTL is in the past relative
#           to real wall time.)
_CREATE_SESSION_LUA = """
if redis.call('EXISTS', KEYS[1]) == 1 then
  return redis.error_reply('session_exists')
end

redis.call('HSET', KEYS[1], 'user_id', ARGV[1])
redis.call('HSET', KEYS[1], 'created_at', ARGV[2])
redis.call('HSET', KEYS[1], 'expires_at', ARGV[3])
redis.call('HSET', KEYS[1], 'expires_at_unix', ARGV[4])
redis.call('HSET', KEYS[1], 'last_used_at', ARGV[5])
redis.call('HSET', KEYS[1], 'last_used_at_unix', ARGV[6])
redis.call('HSET', KEYS[1], 'metadata', ARGV[7])

local expires_unix = tonumber(ARGV[4])
local redis_now_unix = tonumber(ARGV[9])
if expires_unix and redis_now_unix and expires_unix > redis_now_unix then
  redis.call('EXPIREAT', KEYS[1], expires_unix)
end

redis.call('SADD', KEYS[2], ARGV[8])

return 'ok'
"""


# KEYS[1] = auth_svc:session:{session_id}
# KEYS[2] = auth_svc:user_sessions:{user_id}
# ARGV[1] = now_iso (ISO 8601)
# ARGV[2] = now_unix (int)
# ARGV[3] = idle_ttl_seconds (int)
# ARGV[4] = session_id (string, for SREM on expiry)
# ARGV[5] = user_id (string, for SREM on expiry)
#
# Returns flat HGETALL list [k1, v1, k2, v2, ...] on hit, nil on miss/expired.
# Idle uses strict '>' (matches in-memory `_is_idle_expired`).
# Max  uses '>=' (matches in-memory `_is_max_expired`).
# On expiry the key is DELed and SREMed from the user-index.
_GET_SESSION_LUA = """
local data = redis.call('HGETALL', KEYS[1])
if #data == 0 then
  return nil
end

local last_used_unix = tonumber(redis.call('HGET', KEYS[1], 'last_used_at_unix'))
local expires_unix    = tonumber(redis.call('HGET', KEYS[1], 'expires_at_unix'))
local now_unix        = tonumber(ARGV[2])
local idle_ttl_secs   = tonumber(ARGV[3])
if not last_used_unix or not expires_unix or not now_unix or not idle_ttl_secs then
  return nil
end

local is_idle_expired = (now_unix - last_used_unix) > idle_ttl_secs
local is_max_expired  = (now_unix >= expires_unix)

if is_idle_expired or is_max_expired then
  redis.call('DEL', KEYS[1])
  redis.call('SREM', KEYS[2], ARGV[4])
  return nil
end

redis.call('HSET', KEYS[1], 'last_used_at', ARGV[1])
redis.call('HSET', KEYS[1], 'last_used_at_unix', now_unix)
-- Re-read after HSET so the returned data reflects the updated last_used_at.
return redis.call('HGETALL', KEYS[1])
"""


# KEYS[1] = auth_svc:session:{session_id}
# KEYS[2] = auth_svc:user_sessions:{user_id}
# ARGV[1] = session_id
# ARGV[2] = user_id
#
# Returns 1 if existed, 0 if not (matches in-memory revoke_session).
_REVOKE_SESSION_LUA = """
local existed = redis.call('DEL', KEYS[1])
redis.call('SREM', KEYS[2], ARGV[1])
return existed
"""


# KEYS[1] = auth_svc:user_sessions:{user_id}
# ARGV[1] = session key prefix (auth_svc:session:)
#
# Returns the count of sessions deleted.
_REVOKE_ALL_FOR_USER_LUA = """
local members = redis.call('SMEMBERS', KEYS[1])
local count = 0
for _, sid in ipairs(members) do
  if redis.call('DEL', ARGV[1] .. sid) == 1 then
    count = count + 1
  end
end
redis.call('DEL', KEYS[1])
return count
"""


# KEYS[1] = auth_svc:user_sessions:{user_id}
# ARGV[1] = session key prefix (auth_svc:session:)
#
# Recompute user-set TTL to the max of its members' expires_at_unix.
# Reads `expires_at_unix` (integer field) on each session Hash. Deletes the
# user-set if it has no members.
_RECOMPUTE_USER_SET_TTL_LUA = """
local members = redis.call('SMEMBERS', KEYS[1])
if #members == 0 then
  redis.call('DEL', KEYS[1])
  return 0
end

local max_expires_unix = 0
for _, sid in ipairs(members) do
  local unix = tonumber(redis.call('HGET', ARGV[1] .. sid, 'expires_at_unix'))
  if unix and unix > max_expires_unix then
    max_expires_unix = unix
  end
end

local redis_now_unix = tonumber(ARGV[2])
if max_expires_unix > 0 and redis_now_unix and max_expires_unix > redis_now_unix then
  redis.call('EXPIREAT', KEYS[1], max_expires_unix)
end
return max_expires_unix
"""


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------


class RedisSessionManager(SessionManager):
    """SessionManager backed by a single Redis 7 instance.

    The ABC contract (`create_session`, `get_session`, `refresh_session`,
    `revoke_session`, `revoke_all_for_user`) is preserved exactly. All
    operations are routed through Lua scripts registered at construction;
    the audit sink is invoked post-script (never inside Lua).

    `redis_client` must be a `redis.Redis` instance with
    `decode_responses=True` (per design doc §11) so the wrapper treats
    Hash fields as `str`, not `bytes`.

    If `redis_client` is omitted, the manager builds one from the
    `REDIS_URL` env var via `redis.Redis.from_url(...)`.
    """

    def __init__(
        self,
        *,
        clock=None,
        audit_sink=None,
        redis_client: redis.Redis | None = None,
        idle_ttl: timedelta = IDLE_TTL,
        absolute_ttl: timedelta = ABSOLUTE_TTL,
    ) -> None:
        super().__init__(clock=clock, audit_sink=audit_sink, idle_ttl=idle_ttl, absolute_ttl=absolute_ttl)
        self._redis = redis_client if redis_client is not None else self._build_default_client()
        # Register scripts so SHA is cached after the first call.
        self._create_script = self._redis.register_script(_CREATE_SESSION_LUA)
        self._get_script = self._redis.register_script(_GET_SESSION_LUA)
        self._revoke_script = self._redis.register_script(_REVOKE_SESSION_LUA)
        self._revoke_all_script = self._redis.register_script(_REVOKE_ALL_FOR_USER_LUA)
        self._recompute_ttl_script = self._redis.register_script(_RECOMPUTE_USER_SET_TTL_LUA)

    @staticmethod
    def _build_default_client() -> redis.Redis:
        """Build a Redis client from the REDIS_URL env var.

        Defaults to `redis://localhost:6379/0` if REDIS_URL is unset; tests
        pass an explicit `redis_client` fixture so this default is for the
        production wiring only (per design doc §9 hypothesis #5).
        """
        import os
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        return redis.Redis.from_url(url, decode_responses=True)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _session_key(session_id: UUID | str) -> str:
        return _SESSION_KEY + str(session_id)

    @staticmethod
    def _user_set_key(user_id: UUID | str) -> str:
        return _USER_SET_KEY + str(user_id)

    @staticmethod
    def _now_unix(now) -> int:
        """Unix-seconds from the injected clock, used for EXPIREAT.

        Matches the design doc §4.1 contract: the unix-seconds are
        derived FROM the injected clock, not from `time.time()`, so
        the fake clock fully controls expiry.
        """
        return int(now.timestamp())

    @staticmethod
    def _parse_iso(value: str):
        """Parse an ISO 8601 string into a tz-aware datetime.

        Raises ValueError on a malformed timestamp; matches the design
        doc §7 parity invariant.
        """
        from datetime import datetime
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError(f"Naive datetime not allowed: {value!r}")
        return parsed

    def _idle_ttl_seconds(self) -> int:
        return int(self._idle_ttl.total_seconds())

    def _rebuild_session(self, session_id: UUID, flat: list[str]) -> Session:
        """Rebuild a `Session` from the flat HGETALL list returned by Lua.

        The Lua returns `[k1, v1, k2, v2, ...]`; we re-build a dict, parse
        the ISO 8601 timestamps, and JSON-decode the metadata. Raises
        ValueError on any malformed field (matches design doc §7).
        """
        if len(flat) % 2 != 0:
            raise ValueError(f"HGETALL returned odd-length list: {flat!r}")
        data: dict[str, str] = {}
        for i in range(0, len(flat), 2):
            data[flat[i]] = flat[i + 1]
        try:
            return Session(
                session_id=session_id,
                user_id=UUID(data["user_id"]),
                created_at=self._parse_iso(data["created_at"]),
                expires_at=self._parse_iso(data["expires_at"]),
                last_used_at=self._parse_iso(data["last_used_at"]),
                metadata=json.loads(data.get("metadata", "{}")),
            )
        except KeyError as exc:
            raise ValueError(f"Missing required field in session hash: {exc}") from exc

    # -- ABC methods --------------------------------------------------------

    def create_session(self, user_id, *, ttl=None, metadata=None):
        if user_id is None:
            raise ValueError("user_id is required")
        if ttl is not None:
            if ttl <= timedelta(0):
                raise ValueError("ttl must be > 0")
            if ttl > self._idle_ttl:
                raise ValueError(f"ttl must be <= {MAX_INITIAL_TTL}")
        now = self._now()
        session_id = self._new_session_id()
        expires_at = now + self._absolute_ttl
        now_unix = self._now_unix(now)
        expires_unix = self._now_unix(expires_at)
        md_json = json.dumps(dict(metadata) if metadata else {})
        self._create_script(
            keys=[self._session_key(session_id), self._user_set_key(user_id)],
            args=[
                str(user_id),
                now.isoformat(),
                expires_at.isoformat(),
                expires_unix,
                now.isoformat(),
                now_unix,
                md_json,
                str(session_id),
                int(time.time()),
            ],
        )
        # Recompute user-set TTL atomically; the Lua reads expires_at_unix
        # from each member's session Hash.
        self._recompute_ttl_script(
            keys=[self._user_set_key(user_id)],
            args=[_SESSION_KEY, int(time.time())],
        )
        session = Session(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            last_used_at=now,
            metadata=dict(metadata) if metadata else {},
        )
        self._emit(
            "session.created",
            {"session_id": str(session_id), "user_id": str(user_id)},
        )
        return session

    def get_session(self, session_id):
        # We need the user_id for SREM-on-expiry, but we don't have it
        # until we've read the Hash. Two-phase: HGET user_id, then call
        # the Lua. This is racy with a concurrent revoke: a revoke between
        # the HGET and the Lua would make the user_id read stale, but the
        # Lua will see EXISTS=0 and return None anyway, so no incorrect
        # state. The audit-sink contract (no audit on miss) is preserved
        # because we only emit on hit.
        sid = str(session_id)
        user_id_str = self._redis.hget(self._session_key(sid), "user_id")
        if user_id_str is None:
            return None
        now = self._now()
        result = self._get_script(
            keys=[self._session_key(sid), self._user_set_key(user_id_str)],
            args=[
                now.isoformat(),
                self._now_unix(now),
                self._idle_ttl_seconds(),
                sid,
                user_id_str,
            ],
        )
        if result is None:
            return None
        # `decode_responses=True` ensures result entries are `str`, not bytes.
        flat = list(result)
        return self._rebuild_session(session_id, flat)

    def refresh_session(self, session_id):
        # Identical to get_session in behavior; the wrapper emits audit on hit.
        sid = str(session_id)
        user_id_str = self._redis.hget(self._session_key(sid), "user_id")
        if user_id_str is None:
            return None
        now = self._now()
        result = self._get_script(
            keys=[self._session_key(sid), self._user_set_key(user_id_str)],
            args=[
                now.isoformat(),
                self._now_unix(now),
                self._idle_ttl_seconds(),
                sid,
                user_id_str,
            ],
        )
        if result is None:
            return None
        flat = list(result)
        session = self._rebuild_session(session_id, flat)
        self._emit(
            "session.refreshed",
            {"session_id": str(session_id), "user_id": user_id_str},
        )
        return session

    def revoke_session(self, session_id):
        sid = str(session_id)
        user_id_str = self._redis.hget(self._session_key(sid), "user_id")
        if user_id_str is None:
            return False
        existed = self._revoke_script(
            keys=[self._session_key(sid), self._user_set_key(user_id_str)],
            args=[sid, user_id_str],
        )
        existed_int = int(existed)
        if existed_int == 1:
            self._emit(
                "session.revoked",
                {"session_id": str(session_id), "user_id": user_id_str},
            )
            return True
        return False

    def revoke_all_for_user(self, user_id):
        if user_id is None:
            raise ValueError("user_id is required")
        count = int(
            self._revoke_all_script(
                keys=[self._user_set_key(user_id)],
                args=[_SESSION_KEY],
            )
        )
        if count > 0:
            self._emit(
                "session.revoked_all_for_user",
                {"user_id": str(user_id), "count": count},
            )
        return count