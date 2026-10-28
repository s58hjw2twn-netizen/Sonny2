"""Minimal local MCP JSON-RPC protocol handler.

Not a remote server, not authenticated, and not suitable for public exposure.
Only the non-sensitive status tool is callable. Invalid calls fail closed.
"""
from __future__ import annotations

from sonny_one.integration.mcp_contract import call_tool, list_tools

PROTOCOL_VERSION = "2025-03-26"


def handle_message(message: object) -> dict | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "Invalid Request")
    method = message.get("method")
    request_id = message.get("id")
    if not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request")
    if "id" not in message:
        # Ignore notifications; they never authorize any action.
        return None
    if isinstance(request_id, bool) or not isinstance(request_id, (str, int)):
        return _error(None, -32600, "Invalid Request")
    params = message.get("params", {})
    if not isinstance(params, dict):
        return _error(request_id, -32602, "Invalid params")
    if method == "initialize":
        if set(params) != {"protocolVersion", "capabilities", "clientInfo"}:
            return _error(request_id, -32602, "Invalid initialize params")
        if not isinstance(params.get("capabilities"), dict) or not isinstance(params.get("clientInfo"), dict):
            return _error(request_id, -32602, "Invalid initialize params")
        info = params["clientInfo"]
        if not isinstance(info.get("name"), str) or not info["name"] or not isinstance(info.get("version"), str) or not info["version"]:
            return _error(request_id, -32602, "Invalid clientInfo")
        if params.get("protocolVersion") != PROTOCOL_VERSION:
            return _error(request_id, -32602, "Unsupported protocol version")
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "sonny-one-readonly-prototype", "version": "0.1.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        if params:
            return _error(request_id, -32602, "Invalid params")
        result = list_tools()
    elif method == "tools/call":
        if set(params) != {"name", "arguments"}:
            return _error(request_id, -32602, "Invalid params")
        try:
            result = call_tool(params["name"], params["arguments"])
        except PermissionError:
            return _error(request_id, -32602, "Unauthorized tool or arguments")
    else:
        return _error(request_id, -32601, "Method not found")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: object, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
