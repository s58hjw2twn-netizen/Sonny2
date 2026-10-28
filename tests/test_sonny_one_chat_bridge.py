"""Fail-closed read-only bridge boundary tests."""
import unittest
from fastapi.testclient import TestClient
from sonny_one.chat_bridge import create_app

SECRET = "test-only-secret-value-0123456789-abcdef"


class ChatBridgeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(token=SECRET))
        self.auth = {"Authorization": "Bearer " + SECRET}

    def test_requires_secret(self):
        with self.assertRaises(RuntimeError):
            create_app(token="short")

    def test_rejects_bad_revision(self):
        with self.assertRaises(RuntimeError):
            create_app(token=SECRET, verified_sha="main")

    def test_unauthenticated_denied(self):
        for path in ("/v1/status", "/v1/capabilities"):
            for headers in ({}, {"Authorization": "Bearer wrong"}, {"Authorization": "Basic " + SECRET}):
                self.assertEqual(self.client.get(path, headers=headers).status_code, 401)

    def test_status_reports_no_live_verification(self):
        result = self.client.get("/v1/status", headers=self.auth)
        self.assertEqual(result.status_code, 200)
        data = result.json()
        self.assertEqual(data["mode"], "read_only")
        self.assertIsNone(data["verified_revision"])
        self.assertFalse(data["runtime_tests_verified"])
        self.assertFalse(data["autonomous_commits_enabled"])
        self.assertEqual(result.headers["cache-control"], "no-store")

    def test_capabilities_are_declared_not_enabled(self):
        result = self.client.get("/v1/capabilities", headers=self.auth)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["source"], "static_inventory_not_live_proof")
        self.assertTrue(result.json()["capabilities"])

    def test_no_mutation_routes(self):
        for path in ("/v1/status", "/v1/capabilities"):
            self.assertEqual(self.client.post(path, headers=self.auth).status_code, 405)

    def test_operator_rotation_revokes_old_credential(self):
        replacement = "replacement-secret-0123456789-abcdef"
        self.client.app.state.rotate_credential(current_token=SECRET, replacement_token=replacement)
        self.assertEqual(self.client.get("/v1/status", headers=self.auth).status_code, 401)
        self.assertEqual(self.client.get("/v1/status", headers={"Authorization": "Bearer " + replacement}).status_code, 200)

    def test_rotation_rejects_wrong_current_token_and_short_replacement(self):
        with self.assertRaises(PermissionError):
            self.client.app.state.rotate_credential(current_token="wrong", replacement_token="replacement-secret-0123456789-abcdef")
        with self.assertRaises(ValueError):
            self.client.app.state.rotate_credential(current_token=SECRET, replacement_token="short")
        self.assertEqual(self.client.get("/v1/status", headers=self.auth).status_code, 200)

    def test_rotation_has_no_http_endpoint(self):
        self.assertEqual(self.client.post("/v1/rotate", headers=self.auth).status_code, 404)

    def test_supplied_revision_is_not_misrepresented(self):
        client = TestClient(create_app(token=SECRET, verified_sha="a" * 40))
        data = client.get("/v1/status", headers=self.auth).json()
        self.assertEqual(data["revision_attestation"], "operator_supplied_not_independently_checked")


if __name__ == "__main__":
    unittest.main()
