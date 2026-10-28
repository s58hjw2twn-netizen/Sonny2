"""Strict read-only MCP tool contract for Sonny ONE integration.

This is a local protocol adapter, not a network-exposed MCP server.
No write tools, private memory, tokens, or autonomous runner are exposed.
"""
from __future__ import annotations

from sonny_one.integration.bridge_contract import read_public_bridge_status

TOOL_NAME = "sonny_public_status"


def list_tools() -> dict:
    return {
        "tools": [{
            "name": TOOL_NAME,
            "description": "Read non-sensitive Sonny ONE bridge readiness. Does not access personal memory or execute code.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
        }]
    }


def call_tool(name: str, arguments: object) -> dict:
    if name != TOOL_NAME or not isinstance(arguments, dict) or arguments:
        raise PermissionError("MCP tool not authorized")
    return {
        "content": [{"type": "text", "text": _encode_status()}],
        "isError": False,
    }


def _encode_status() -> str:
    import json
    return json.dumps(read_public_bridge_status(), sort_keys=True, separators=(",", ":"))
