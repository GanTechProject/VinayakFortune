"""Canonical ToolManifest — plugin-svc cross-service canary.

Cross-service canary with agent-runtime (Architect #6 §13) and
reporting-svc (Architect #12 §11.4). Byte-identical import test
required at services/plugin-svc/tests/test_006_tool_manifest_byte_identical_import_test.py.

Per Architect #9 §12 (Doc 12 §4 L55-77) and Architect #12 §11.4 verification.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ToolAuth(BaseModel):
    """Doc 12 §4 L62: auth: { type, secret_ref }."""

    type: Literal["api_key", "service_token", "oauth", "none"]
    secret_ref: str


class ToolCost(BaseModel):
    """Doc 12 §4 L63: cost: { per_call_usd, weight }."""

    per_call_usd: float = Field(ge=0.0)
    weight: int = Field(ge=0)


class ToolRateLimit(BaseModel):
    """Doc 12 §4 L74: rate_limit: { per_minute, per_hour }."""

    per_minute: int = Field(gt=0)
    per_hour: int = Field(gt=0)


class ToolRetry(BaseModel):
    """Doc 12 §4 L76: retry: { max, backoff }."""

    max: int = Field(ge=0)
    backoff: Literal["exponential", "linear", "none"]


class ToolManifest(BaseModel):
    """Canonical plugin-svc ToolManifest."""

    id: str  # T-MARKET-DATA-FETCHER
    name: str  # "Market Data Fetcher"
    version: str  # semver, e.g. "1.2.0"
    description: str
    risk_level: Literal["low", "medium", "high"]  # Doc 12 §4 L65
    pii_risk: bool  # Doc 12 §4 L66
    input_schema: dict  # JSON Schema, Doc 12 §4 L67
    output_schema: dict  # JSON Schema, Doc 12 §4 L68
    auth: ToolAuth
    cost: ToolCost
    rate_limit: ToolRateLimit
    timeout_ms: int = Field(gt=0)
    retry: ToolRetry
    owner: str  # "ai-platform"


__all__ = ["ToolManifest", "ToolAuth", "ToolCost", "ToolRateLimit", "ToolRetry"]
