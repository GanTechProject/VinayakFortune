"""test_003 — ToolManifest cross-service canary.

Per Architect #9 §12.4 + Architect #12 §11.4 (the ToolManifest byte-identical
discipline). agent-runtime's MCP gateway validates input against the
canonical manifest; it does NOT re-define the manifest.
"""

from __future__ import annotations


def test_tool_manifest_field_set() -> None:
    """ToolManifest must have the canonical 14-field shape."""
    from services.agent_runtime.app.contracts.tool_manifest import ToolManifest as ArTM
    from services.plugin_svc.app.contracts.tool_manifest import ToolManifest

    expected_fields = {
        "id", "name", "version", "description", "risk_level", "pii_risk",
        "input_schema", "output_schema", "auth", "cost", "rate_limit",
        "timeout_ms", "retry", "owner",
    }
    assert set(ToolManifest.model_fields.keys()) == expected_fields
    assert ToolManifest.model_fields == ArTM.model_fields


def test_tool_manifest_uses_jsonschema_envelope() -> None:
    """DRIFT-9.6: input_schema / output_schema are dict (JsonSchema), not nested models."""
    from services.plugin_svc.app.contracts.tool_manifest import ToolManifest

    fields = ToolManifest.model_fields
    assert fields["input_schema"].annotation is dict
    assert fields["output_schema"].annotation is dict


def test_tool_manifest_import_is_plugin_svc() -> None:
    """agent-runtime's ToolManifest is the canonical plugin-svc ToolManifest."""
    import services.agent_runtime.app.contracts.tool_manifest as ar_tm_mod
    import services.plugin_svc.app.contracts.tool_manifest as plugin_tm_mod

    assert ar_tm_mod.ToolManifest is plugin_tm_mod.ToolManifest
