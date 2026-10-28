import asyncio
import json
import unittest

from sonny_one.integration.private_mcp_asgi import private_mcp_app


TOKEN = "b" * 48


def request(token=None, method="POST", path="/private/mcp", body=None, expected=TOKEN):
    sent = []
    payload = json.dumps(body or {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}
    async def send(event):
        sent.append(event)
    headers = [(b"content-type", b"application/json")]
    if token is not None:
        headers.append((b"authorization", b"Bearer " + token.encode()))
    asyncio.run(private_mcp_app({"type": "http", "method": method, "path": path, "headers": headers}, receive, send, expected_token=expected))
    return sent[0]["status"], json.loads(sent[1]["body"])


class PrivateMcpAsgiTests(unittest.TestCase):
    def test_missing_and_wrong_tokens_denied(self):
        self.assertEqual(request()[0], 401)
        self.assertEqual(request("wrong")[0], 401)
        self.assertEqual(request(TOKEN, expected=None)[0], 401)

    def test_authorized_read_only_tool_list(self):
        status, result = request(TOKEN)
        self.assertEqual(status, 200)
        self.assertEqual([x["name"] for x in result["result"]["tools"]], ["sonny_public_status"])

    def test_authorized_write_attempt_denied(self):
        status, result = request(TOKEN, body={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "development.commit", "arguments": {}}})
        self.assertEqual(status, 200)
        self.assertEqual(result["error"]["code"], -32602)

    def test_invalid_json_denied_without_protocol_execution(self):
        import asyncio
        sent = []
        async def receive():
            return {"type": "http.request", "body": b"{broken", "more_body": False}
        async def send(event):
            sent.append(event)
        asyncio.run(private_mcp_app({
            "type": "http", "method": "POST", "path": "/private/mcp",
            "headers": [(b"authorization", b"Bearer " + TOKEN.encode()), (b"content-type", b"application/json")],
        }, receive, send, expected_token=TOKEN))
        self.assertEqual(sent[0]["status"], 400)

    def test_oversized_request_rejected(self):
        import asyncio
        sent = []
        async def receive():
            return {"type": "http.request", "body": b"x" * 65537, "more_body": False}
        async def send(event):
            sent.append(event)
        asyncio.run(private_mcp_app({
            "type": "http", "method": "POST", "path": "/private/mcp",
            "headers": [(b"authorization", b"Bearer " + TOKEN.encode())],
        }, receive, send, expected_token=TOKEN))
        self.assertEqual(sent[0]["status"], 413)

    def test_missing_content_type_rejected(self):
        import asyncio
        sent = []
        async def receive():
            return {"type": "http.request", "body": b"{}", "more_body": False}
        async def send(event):
            sent.append(event)
        asyncio.run(private_mcp_app({
            "type": "http", "method": "POST", "path": "/private/mcp",
            "headers": [(b"authorization", b"Bearer " + TOKEN.encode())],
        }, receive, send, expected_token=TOKEN))
        self.assertEqual(sent[0]["status"], 415)

    def test_unavailable_routes_denied(self):
        self.assertEqual(request(TOKEN, method="GET")[0], 404)
        self.assertEqual(request(TOKEN, path="/private/memory")[0], 404)


if __name__ == "__main__":
    unittest.main()
