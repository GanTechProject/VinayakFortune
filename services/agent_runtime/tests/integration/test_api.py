"""Integration tests for the public REST API (app/api/events.py).

Covers:
- POST /runs          — plan union validation + run-type-derived default plan (BUG F)
- GET  /runs/{id}     — workspace-scoped read (BUG G)
- DELETE /runs/{id}   — workspace-scoped cancel (BUG G)
- GET  /healthz       — liveness probe returns {"status":"ok"}
"""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from services.agent_runtime.app.api.events import _RUN_STORE
from services.agent_runtime.app.main import create_app


def _fresh_client() -> TestClient:
    """Return a TestClient bound to a fresh app; clears the in-process store."""
    _RUN_STORE.clear()
    return TestClient(create_app())


def _run_payload(workspace_id: UUID, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "goal": "validate market opportunity",
        "workspace_id": str(workspace_id),
        "user_id": str(uuid4()),
        "run_type": "validation_standard",
    }
    payload.update(overrides)
    return payload


def test_post_run_with_validation_plan_succeeds() -> None:
    """BUG F: a validation plan payload must validate against the Plan union (201)."""
    client = _fresh_client()
    resp = client.post(
        "/runs",
        json=_run_payload(
            workspace_id=uuid4(),
            plan={
                "plan_type": "validation",
                "dimensions": ["market"],
                "rubric_version": "v1.0",
            },
        ),
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "running"


def test_post_run_default_plan_derived_from_run_type_validation() -> None:
    """BUG F: run_type=validation_standard with no plan derives a ValidationPlan."""
    client = _fresh_client()
    resp = client.post("/runs", json=_run_payload(workspace_id=uuid4()))
    assert resp.status_code == 201
    run_id = UUID(resp.json()["run_id"])
    assert _RUN_STORE[run_id].plan.plan_type == "validation"


def test_post_run_default_plan_derived_from_run_type_discovery() -> None:
    """BUG F: run_type=discovery_standard with no plan derives a DiscoveryPlan."""
    client = _fresh_client()
    resp = client.post(
        "/runs",
        json=_run_payload(workspace_id=uuid4(), run_type="discovery_standard"),
    )
    assert resp.status_code == 201
    run_id = UUID(resp.json()["run_id"])
    assert _RUN_STORE[run_id].plan.plan_type == "discovery"


def test_post_run_default_plan_derived_from_run_type_full_report() -> None:
    """BUG F: run_type=full_report with no plan derives a ReportPlan."""
    client = _fresh_client()
    resp = client.post(
        "/runs",
        json=_run_payload(workspace_id=uuid4(), run_type="full_report"),
    )
    assert resp.status_code == 201
    run_id = UUID(resp.json()["run_id"])
    assert _RUN_STORE[run_id].plan.plan_type == "report"


def test_get_run_scoped_by_workspace() -> None:
    """BUG G: GET returns 200 for the owning workspace, 404 for another."""
    client = _fresh_client()
    ws_a, ws_b = uuid4(), uuid4()
    run_id = UUID(client.post("/runs", json=_run_payload(workspace_id=ws_a)).json()["run_id"])

    ok = client.get(f"/runs/{run_id}", params={"workspace_id": str(ws_a)})
    assert ok.status_code == 200
    assert ok.json()["workspace_id"] == str(ws_a)

    forbidden = client.get(f"/runs/{run_id}", params={"workspace_id": str(ws_b)})
    assert forbidden.status_code == 404


def test_cancel_run_scoped_by_workspace() -> None:
    """BUG G: DELETE is 404 for a non-owner and 204 for the owner."""
    client = _fresh_client()
    ws_a, ws_b = uuid4(), uuid4()
    run_id = UUID(client.post("/runs", json=_run_payload(workspace_id=ws_a)).json()["run_id"])

    wrong = client.delete(f"/runs/{run_id}", params={"workspace_id": str(ws_b)})
    assert wrong.status_code == 404
    assert run_id in _RUN_STORE

    right = client.delete(f"/runs/{run_id}", params={"workspace_id": str(ws_a)})
    assert right.status_code == 204
    assert run_id not in _RUN_STORE


def test_get_run_healthz() -> None:
    """GET /healthz returns the canonical liveness body {"status":"ok"}."""
    client = _fresh_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
