"""Unit tests for the hello-world service.

These are the RED tests for AC-1.1 in issue #4: the sample service builds,
lints, tests, and runs in Docker locally AND in the staging cluster.

The tests assert the *exact* response shape, not just "returns 200" — a mutation
that changed the JSON contract to return `{"msg": ...}` instead of
`{"message": ...}` should fail this test.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_200() -> None:
    """The root path is reachable and returns HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


def test_root_returns_expected_json_shape() -> None:
    """The response body has the expected fields (mutation-testing mindset)."""
    response = client.get("/")
    body = response.json()
    assert "message" in body
    assert "service" in body
    assert "version" in body
    assert body["service"] == "hello-world"
    # version is a string of the form "X.Y.Z"
    parts = body["version"].split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_healthz_returns_200_and_healthy() -> None:
    """REQ-PLAT-0010: health endpoint exists and is reachable."""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_returns_200_when_ready() -> None:
    """REQ-PLAT-0010: readiness endpoint exists and is reachable."""
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"ready": True}
