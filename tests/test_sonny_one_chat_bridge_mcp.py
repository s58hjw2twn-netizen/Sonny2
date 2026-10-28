"""MCP boundary tests: authentication, protocol, no side effects."""
import json
import unittest
from fastapi.testclient import TestClient
from sonny_one.chat_bridge_mcp import create_mcp_app

TOKEN = "disposable-test-token-0123456789-abcdef"


class MCPTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_mcp_app(token=TOKEN))
        self.headers = {"Authorization": "Bearer " + TOKEN}
        self.headers["Content-Type"] = "application/json"

    def call(self, method, params=None, headers=None):
        return self.client.post("/mcp", headers=self.headers if headers is None else headers,
                                json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})

    def test_no_weak_secret(self):
        with self.assertRaises(RuntimeError):
            create_mcp_app(token="short")

    def test_authentication_required(self):
        self.assertEqual(self.call("tools/list", headers={"Content-Type": "application/json"}).status_code, 401)
        self.assertEqual(self.call("tools/list", headers={"Authorization": "Bearer invalid", "Content-Type": "application/json"}).status_code, 401)

    def test_initialization_and_tools(self):
        self.assertEqual(self.call("initialize").json()["result"]["capabilities"], {"tools": {}})
        tools = self.call("tools/list").json()["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, {"sonny_status", "sonny_capabilities"})
        self.assertEqual(self.call("ping").json()["result"], {})

    def test_read_only_calls(self):
        status = self.call("tools/call", {"name": "sonny_status"}).json()["result"]["content"][0]["text"]
        self.assertFalse(json.loads(status)["connected_to_chatgpt"])
        caps = self.call("tools/call", {"name": "sonny_capabilities"}).json()["result"]["content"][0]["text"]
        self.assertEqual(json.loads(caps)["source"], "static_inventory_not_live_proof")

    def test_mutation_not_supported(self):
        self.assertEqual(self.call("tools/call", {"name": "github_write"}).json()["error"]["code"], -32602)
        self.assertEqual(self.call("tools/call", {"name": "sonny_status", "arguments": {"x": 1}}).json()["error"]["code"], -32602)
        self.assertEqual(self.client.get("/mcp", headers=self.headers).status_code, 405)

    def test_no_unrecognized_methods(self):
        self.assertEqual(self.call("resources/list").json()["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
