"""Read-only MCP-over-HTTP interoperability checks for the existing local bridge.

These tests do not establish production transport, OAuth, hosting or a live
ChatGPT connection.
"""
import asyncio
import json
import unittest

from sonny_one.integration.private_mcp_asgi import private_mcp_app

TOKEN = "synthetic-test-token-not-for-production-123456789"


async def invoke(message, *, token=TOKEN, origin=False):
    sent = []
    body = json.dumps(message).encode()
    headers = [(b"authorization", ("Bearer " + token).encode()),
               (b"content-type", b"application/json"),
               (b"content-length", str(len(body)).encode())]
    if origin:
        headers.append((b"origin", b"https://untrusted.example"))
    delivered = False

    async def receive():
        nonlocal delivered
        if delivered:
            raise AssertionError("unexpected second read")
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(event):
        sent.append(event)

    await private_mcp_app({"type": "http", "method": "POST", "path": "/private/mcp", "headers": headers}, receive, send, expected_token=TOKEN)
    return sent[0]["status"], json.loads(sent[1]["body"])


class PrivateMcpInteropTests(unittest.TestCase):
    def test_initialize_list_and_status_call(self):
        async def run():
            status, init = await invoke({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "synthetic-client", "version": "1.0"}}})
            self.assertEqual(status, 200)
            self.assertEqual(init["result"]["protocolVersion"], "2025-03-26")
            status, listed = await invoke({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            self.assertEqual(status, 200)
            self.assertEqual([t["name"] for t in listed["result"]["tools"]], ["sonny_public_status"])
            status, called = await invoke({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                "name": "sonny_public_status", "arguments": {}}})
            self.assertEqual(status, 200)
            self.assertIn("result", called)
        asyncio.run(run())

    def test_bad_token_is_rejected(self):
        status, payload = asyncio.run(invoke({"jsonrpc": "2.0", "id": 1, "method": "ping"}, token="wrong"))
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_origin_is_rejected(self):
        status, payload = asyncio.run(invoke({"jsonrpc": "2.0", "id": 1, "method": "ping"}, origin=True))
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "origin_not_allowed")

    def test_write_tool_is_rejected(self):
        status, payload = asyncio.run(invoke({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "github_commit", "arguments": {}}))
        self.assertEqual(status, 200)
        self.assertIn("error", payload)
        self.assertNotIn("result", payload)


if __name__ == "__main__":
    unittest.main()
