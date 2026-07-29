"""MCP gateway integration tests (Architect #6 §13 test_021..test_026)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from services.agent_runtime.app.mcp.gateway import (
    InvocationContext,
    InvocationResult,
    MCPGateway,
    StaticToolRegistry,
)
from services.agent_runtime.app.mcp.policy import (
    PolicyViolation,
)
from services.plugin_svc.app.contracts.tool_manifest import (
    ToolAuth,
    ToolCost,
    ToolManifest,
    ToolRateLimit,
    ToolRetry,
)


def _manifest() -> ToolManifest:
    return ToolManifest(
        id="T-MARKET-DATA-FETCHER",
        name="Market Data Fetcher",
        version="1.0.0",
        description="Fetches market data.",
        risk_level="low",
        pii_risk=False,
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={"type": "object"},
        auth=ToolAuth(type="api_key", secret_ref="provider/marketdata/api_key"),
        cost=ToolCost(per_call_usd=0.02, weight=1),
        rate_limit=ToolRateLimit(per_minute=60, per_hour=1000),
        timeout_ms=5000,
        retry=ToolRetry(max=2, backoff="exponential"),
        owner="ai-platform",
    )


def _ctx() -> InvocationContext:
    return InvocationContext(
        run_id=uuid4(),
        step_id=uuid4(),
        workspace_id=uuid4(),
        user_id=uuid4(),
        agent_id="AGT-RSRCH-MARKET",
    )


@pytest.mark.asyncio
async def test_mcp_gateway_rejects_unregistered_tool() -> None:
    """Per Architect #6 §13 test_024: manifest miss → reject."""
    gw = MCPGateway(agent_id="AGT-RSRCH-MARKET")
    with pytest.raises(PolicyViolation) as ei:
        await gw.call(
            tool_id="T-NOT-REGISTERED",
            input={"query": "x"},
            ctx=_ctx(),
        )
    assert ei.value.code == "tool_not_registered"


@pytest.mark.asyncio
async def test_mcp_gateway_enforces_per_call_pii_policy() -> None:
    """Per Architect #6 §13 test_022: PII in input → reject before external egress."""
    gw = MCPGateway(
        agent_id="AGT-RSRCH-MARKET",
        registry=StaticToolRegistry([_manifest()]),
    )
    with pytest.raises(PolicyViolation) as ei:
        await gw.call(
            tool_id="T-MARKET-DATA-FETCHER",
            input={"query": "contact me at user@example.com"},
            ctx=_ctx(),
        )
    assert ei.value.code == "pii_policy_violation"


@pytest.mark.asyncio
async def test_mcp_gateway_enforces_workspace_allow_deny() -> None:
    """Per Architect #6 §13 test_021: per-workspace allow/deny."""
    class DenyPolicy:
        def is_allowed(self, tool_id: str, workspace_id: str) -> bool:
            return False

    gw = MCPGateway(
        agent_id="AGT-RSRCH-MARKET",
        registry=StaticToolRegistry([_manifest()]),
        workspace_policy=DenyPolicy(),
    )
    with pytest.raises(PolicyViolation) as ei:
        await gw.call(
            tool_id="T-MARKET-DATA-FETCHER",
            input={"query": "x"},
            ctx=_ctx(),
        )
    assert ei.value.code == "workspace_denied"


@pytest.mark.asyncio
async def test_mcp_gateway_returns_429_on_rate_limit() -> None:
    """Per Architect #6 §13 test_023: rate limit → 429 + retry_after."""
    class AlwaysRateLimited:
        def allow(self, tool_id: str, workspace_id: str, run_id: str) -> bool:
            return False

    gw = MCPGateway(
        agent_id="AGT-RSRCH-MARKET",
        registry=StaticToolRegistry([_manifest()]),
        rate_limiter=AlwaysRateLimited(),
    )
    with pytest.raises(PolicyViolation) as ei:
        await gw.call(
            tool_id="T-MARKET-DATA-FETCHER",
            input={"query": "x"},
            ctx=_ctx(),
        )
    assert ei.value.code == "rate_limited"
    assert ei.value.retry_after_s == 60


@pytest.mark.asyncio
async def test_mcp_gateway_traces_otel_span_per_call() -> None:
    """Per Architect #6 §13 test_025: OTel span per call."""
    gw = MCPGateway(
        agent_id="AGT-RSRCH-MARKET",
        registry=StaticToolRegistry([_manifest()]),
    )
    await gw.call(tool_id="T-MARKET-DATA-FETCHER", input={"query": "x"}, ctx=_ctx())
    assert len(gw.spans) == 1
    span = gw.spans[0]
    assert span["tool_id"] == "T-MARKET-DATA-FETCHER"
    assert span["agent_id"] == "AGT-RSRCH-MARKET"
    assert "timestamp" in span


@pytest.mark.asyncio
async def test_mcp_gateway_succeeds_for_registered_tool() -> None:
    """The happy path: a registered tool with no PII → InvocationResult."""
    gw = MCPGateway(
        agent_id="AGT-RSRCH-MARKET",
        registry=StaticToolRegistry([_manifest()]),
    )
    result = await gw.call(
        tool_id="T-MARKET-DATA-FETCHER",
        input={"query": "TAM EV charging 2026"},
        ctx=_ctx(),
    )
    assert isinstance(result, InvocationResult)
    assert result.cost_usd > 0
    assert result.audit_event_id is not None
