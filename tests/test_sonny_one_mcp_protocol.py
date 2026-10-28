import json
import unittest

from sonny_one.integration.mcp_protocol import PROTOCOL_VERSION, handle_message


def rpc(method, params=None, request_id=1):
    return handle_message({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})


class McpProtocolTests(unittest.TestCase):
    def test_initialize_and_tool_listing(self):
        initialized = rpc("initialize", {"protocolVersion": PROTOCOL_VERSION})
        self.assertEqual(initialized["result"]["protocolVersion"], PROTOCOL_VERSION)
        tools = rpc("tools/list")["result"]["tools"]
        self.assertEqual([t["name"] for t in tools], ["sonny_public_status"])

    def test_public_status_call(self):
        response = rpc("tools/call", {"name": "sonny_public_status", "arguments": {}})
        status = json.loads(response["result"]["content"][0]["text"])
        self.assertFalse(status["runtime_connected"])

    def test_denies_write_tools_and_injection(self):
        for params in [
            {"name": "development.commit", "arguments": {}},
            {"name": "sonny_public_status", "arguments": {"admin": True}},
            {"name": "sonny_public_status", "arguments": {},"override": True},
        ]:
            with self.subTest(params=params):
                self.assertEqual(rpc("tools/call", params)["error"]["code"], -32602)

    def test_notifications_cannot_execute(self):
        self.assertIsNone(handle_message({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "sonny_public_status", "arguments": {}}}))

    def test_invalid_protocol_and_method_rejected(self):
        self.assertEqual(rpc("initialize", {"protocolVersion": "2024-11-05"})["error"]["code"], -32602)
        self.assertEqual(rpc("development.commit")["error"]["code"], -32601)
        self.assertEqual(rpc("tools/list", {"admin": True})["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
