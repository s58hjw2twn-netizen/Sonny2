import unittest

from sonny_one.integration.bridge_contract import (
    RESEARCH_BRANCH, authorize_capability, capability_manifest, read_public_bridge_status,
)


class BridgeContractTests(unittest.TestCase):
    def test_no_capabilities_enabled_by_default(self):
        manifest = capability_manifest()
        self.assertEqual(manifest["research_branch"], RESEARCH_BRANCH)
        self.assertFalse(manifest["runtime_connected"])
        self.assertFalse(manifest["unattended_development_enabled"])
        self.assertTrue(all(not value["enabled"] for value in manifest["capabilities"].values()))

    def test_mutating_manifest_cannot_change_policy(self):
        first = capability_manifest()
        first["capabilities"]["development.commit"]["enabled"] = True
        self.assertFalse(capability_manifest()["capabilities"]["development.commit"]["enabled"])

    def test_forged_runtime_evidence_does_not_authorize(self):
        for name in capability_manifest()["capabilities"]:
            with self.subTest(name=name):
                with self.assertRaises(PermissionError):
                    authorize_capability(name, runtime_evidence={
                        "authenticated": True, "sandbox_verified": True,
                        "signed": True, "owner_approved": True,
                    })

    def test_public_status_never_exposes_private_data_or_activation(self):
        status = read_public_bridge_status()
        self.assertEqual(status["status"], "integration_contract_only")
        self.assertFalse(status["runtime_connected"])
        self.assertFalse(status["unattended_development_enabled"])
        self.assertEqual(status["enabled_capabilities"], [])
        self.assertNotIn("memory", status)
        self.assertNotIn("credentials", status)

    def test_unknown_capability_fails_closed(self):
        with self.assertRaises(PermissionError):
            authorize_capability("development.override")


if __name__ == "__main__":
    unittest.main()
