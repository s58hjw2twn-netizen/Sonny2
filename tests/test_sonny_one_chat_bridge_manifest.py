"""Verify the tool manifest never advertises powers the bridge lacks."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BridgeManifestTests(unittest.TestCase):
    def test_manifest_is_read_only_and_not_connected(self):
        data = json.loads((ROOT / "sonny_one" / "chat_bridge_manifest.json").read_text())
        self.assertEqual(data["connection_status"], "not_registered")
        self.assertFalse(data["transport"]["remote_use_allowed"])
        self.assertTrue(data["transport"]["requires_https_before_remote_use"])
        self.assertEqual({t["path"] for t in data["tools"]}, {"/v1/status", "/v1/capabilities"})
        self.assertTrue(all(t["method"] == "GET" and t["read_only"] for t in data["tools"]))
        self.assertIn("github_write", data["forbidden"])
        self.assertIn("memory_read", data["forbidden"])

    def test_manifest_does_not_claim_verified_live_capabilities(self):
        data = json.loads((ROOT / "sonny_one" / "chat_bridge_manifest.json").read_text())
        self.assertIn("static capability inventory", data["tools"][1]["description"])
        self.assertIn("plugin_registration", data["approval_required_before"])


if __name__ == "__main__":
    unittest.main()
