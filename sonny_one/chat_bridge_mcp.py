"""Local-only read-only MCP JSON-RPC prototype for Sonny ONE.

Not an internet-facing MCP server. No OAuth, sessions, SSE, streaming, or
ChatGPT registration. An authenticated client may inspect static capabilities.
"""
import hmac
import os

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from sonny_one.capability_inventory import capability_inventory

TOOLS = (
    {"name": "sonny_status", "description": "Report local bridge restrictions, not independently verified runtime status.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "sonny_capabilities", "description": "Read static capability inventory, not live execution proof.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
)


def create_mcp_app(*, token=None):
    secret = token if token is not None else os.getenv("SONNY_CHAT_BRIDGE_TOKEN", "")
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError("A private token of at least 32 characters is required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        # This application must remain on a loopback-only listener; Host is not
        # a trustworthy substitute for network isolation.
        from ipaddress import ip_address
        try:
            local = request.client is not None and ip_address(request.client.host).is_loopback
        except ValueError:
            local = False
        if not local:
            response = JSONResponse({"error": "Loopback only"}, status_code=403)
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.post("/mcp")
    async def mcp(request: Request, authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer ") or not hmac.compare_digest(authorization[7:], secret):
            raise HTTPException(status_code=401, detail="Authentication required")
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        try:
            payload = await request.json()
        except ValueError:
            raise HTTPException(status_code=400, detail="Malformed JSON")
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0" or not isinstance(payload.get("method"), str):
            return JSONResponse({"jsonrpc": "2.0", "id": payload.get("id") if isinstance(payload, dict) else None, "error": {"code": -32600, "message": "Invalid Request"}})
        method, ident = payload["method"], payload.get("id")
        if method == "notifications/initialized" and "id" not in payload:
            from fastapi import Response
            return Response(status_code=202)
        if "id" not in payload or not isinstance(ident, (str, int)) or isinstance(ident, bool):
            return JSONResponse({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}})
        params = payload.get("params", {})
        if not isinstance(params, dict):
            result = {"error": {"code": -32602, "message": "Invalid params"}}
        elif method == "initialize":
            result = {"result": {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "sonny-one-local-read-only", "version": "0.1.0"}}}
        elif method == "ping":
            result = {"result": {}}
        elif method == "tools/list":
            result = {"result": {"tools": list(TOOLS)}}
        elif method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            if not isinstance(args, dict) or args:
                result = {"error": {"code": -32602, "message": "Invalid tool arguments"}}
            elif name == "sonny_status":
                result = {"result": {"content": [{"type": "text", "text": '{"mode":"local_read_only","runtime_tests_verified":false,"connected_to_chatgpt":false}'}]}}
            elif name == "sonny_capabilities":
                import json
                result = {"result": {"content": [{"type": "text", "text": json.dumps({"source": "static_inventory_not_live_proof", "capabilities": capability_inventory()})}]}}
            else:
                result = {"error": {"code": -32602, "message": "Unknown tool"}}
        else:
            result = {"error": {"code": -32601, "message": "Method not found"}}
        return JSONResponse({"jsonrpc": "2.0", "id": ident, **result})

    return app
