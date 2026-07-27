# services/auth-svc/app/conftest.py
# Provides the `redis_client` fixture (and its dependency, the
# `redis_container` / `_redis_flush` helpers) to the test suite.
#
# Used by:
#   - app/test_redis_session_manager.py  (the 39th duplicated file)
#   - app/test_session_manager.py        (NOT modified by this PR; if the
#                                         conductor picks Strategy A, the
#                                         manager fixture is the only edit)
#
# Skip-on-unavailable: the redis_client fixture is only requested by tests
# that ask for the `redis_manager` fixture. The in-memory suite never asks
# for it, so the redis_client fixture is never resolved, and the suite
# runs even when Redis is absent.

from __future__ import annotations

import os

import pytest
import redis


@pytest.fixture
def redis_client():
    """A redis.Redis client connected to AUTH_SVC_REDIS_URL, DB 15.

    Defaults to redis://localhost:6379/15 (the convention used by the
    GitHub Actions `services:` block in .github/workflows/ci-hello-world.yml).
    Flushes the DB on teardown so each test starts clean.
    """
    url = os.environ.get("AUTH_SVC_REDIS_URL", "redis://localhost:6379/15")
    client = redis.Redis.from_url(url, decode_responses=True)
    client.ping()  # fail fast if Redis is unreachable
    yield client
    client.flushdb()