import io
import json
import unittest

from sonny_one.integration.mcp_stdio import serve_stream


class McpStdioTests(unittest.TestCase):
    def test_round_trip_and_no_write_tool(self):
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0"}}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "sonny_public_status", "arguments": {}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "development.commit", "arguments": {}}},
        ]
        source = io.StringIO("".join(json.dumps(x) + "\n" for x in requests))
        sink = io.StringIO()
        serve_stream(source, sink)
        replies = [json.loads(x) for x in sink.getvalue().splitlines()]
        self.assertEqual(len(replies), 4)
        self.assertEqual([x["name"] for x in replies[1]["result"]["tools"]], ["sonny_public_status"])
        self.assertFalse(json.loads(replies[2]["result"]["content"][0]["text"])["runtime_connected"])
        self.assertEqual(replies[3]["error"]["code"], -32602)

    def test_malformed_oversized_and_notifications_silent(self):
        messages = "not-json\n" + ("x" * 65537) + "\n" + json.dumps({
            "jsonrpc": "2.0", "method": "notifications/initialized"
        }) + "\n"
        sink = io.StringIO()
        serve_stream(io.StringIO(messages), sink)
        self.assertEqual(sink.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
