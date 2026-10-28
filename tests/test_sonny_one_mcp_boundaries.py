"""Protocol-level negative tests for the Sonny ONE local MCP adapter."""
import unittest

from sonny_one.integration.mcp_protocol import handle_message


class McpProtocolBoundaryTests(unittest.TestCase):
    def test_rejects_non_json_rpc_envelopes(self):
        for message in [None, [], {}, {"jsonrpc": "1.0", "id": 1, "method": "ping"}, {"jsonrpc": "2.0", "id": True, "method": "ping"}]:
            with self.subTest(message=message):
                response = handle_message(message)
                self.assertEqual(response["error"]["code"], -32600)

    def test_does_not_accept_unlisted_operations(self):
        for method in ["resources/list", "resources/read", "prompts/list", "logging/setLevel", "development.commit"]:
            with self.subTest(method=method):
                response = handle_message({"jsonrpc": "2.0", "id": 1, "method": method})
                self.assertEqual(response["error"]["code"], -32601)

    def test_tool_call_rejects_extra_properties(self):
        message = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "sonny_public_status", "arguments": {}, "write": True},
        }
        self.assertEqual(handle_message(message)["error"]["code"], -32602)


if __name__ == "__main__":
    unittest.main()
