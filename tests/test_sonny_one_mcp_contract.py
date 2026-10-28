import json
import unittest

from sonny_one.integration.mcp_contract import TOOL_NAME, call_tool, list_tools


class McpContractTests(unittest.TestCase):
    def test_only_public_status_tool_advertised(self):
        tools = list_tools()["tools"]
        self.assertEqual([t["name"] for t in tools], [TOOL_NAME])
        self.assertTrue(tools[0]["annotations"]["readOnlyHint"])
        self.assertFalse(tools[0]["annotations"]["destructiveHint"])
        self.assertFalse(tools[0]["inputSchema"]["additionalProperties"])

    def test_status_call_is_non_sensitive_and_not_connected(self):
        response = call_tool(TOOL_NAME, {})
        data = json.loads(response["content"][0]["text"])
        self.assertFalse(data["runtime_connected"])
        self.assertFalse(data["unattended_development_enabled"])
        self.assertEqual(data["enabled_capabilities"], [])

    def test_unknown_and_argument_injection_denied(self):
        for name, args in [
            ("development.commit", {}),
            (TOOL_NAME, {"admin": True}),
            (TOOL_NAME, None),
            (TOOL_NAME, []),
        ]:
            with self.subTest(name=name, args=args):
                with self.assertRaises(PermissionError):
                    call_tool(name, args)


if __name__ == "__main__":
    unittest.main()
