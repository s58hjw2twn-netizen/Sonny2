"""End-to-end authenticated private inference tests with a simulated model."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sonny.auth import create_access_token
from sonny_one.inference import Request, Response, InferenceFailure, InferenceTimeout
from sonny_one.private_provider import install_private_provider, reset_private_provider
from sonny_one.rate_limit import LocalRateLimiter
from sonny_one.web_app import app


class MockModel:
    def generate(self, incoming: Request) -> Response:
        return Response(text="Simulated answer to: " + incoming.prompt, model_id="mock-model", demo=False)


class MockFailure:
    def generate(self, incoming: Request) -> Response:
        raise RuntimeError("sensitive upstream diagnostic")


class PrivateInferenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        reset_private_provider()
        self.client = TestClient(app)
        self.env = patch.dict(os.environ, {"SONNY_AUTH_SECRET": "local-test-secret"})
        self.env.start()
        self.headers = {"Authorization": "Bearer " + create_access_token("integration-user")}

    def tearDown(self):
        reset_private_provider()
        self.env.stop()

    def test_mock_model_replies_only_after_authentication(self):
        install_private_provider(MockModel(), approved=True)
        with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=10)):
            unauthorized = self.client.post("/api/inference/private", json={"message": "hello"})
            authorized = self.client.post("/api/inference/private", json={"message": "hello"}, headers=self.headers)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized.json()["text"], "Simulated answer to: hello")
        self.assertEqual(authorized.json()["mode"], "private-inference")
        self.assertTrue(authorized.json()["model_connected"])
        self.assertEqual(authorized.json()["model_id"], "mock-model")

    def test_provider_exception_is_sanitized(self):
        install_private_provider(MockFailure(), approved=True)
        with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=10)):
            response = self.client.post("/api/inference/private", json={"message": "hello"}, headers=self.headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive", response.text)

    def test_unapproved_activation_fails_closed(self):
        with self.assertRaises(PermissionError):
            install_private_provider(MockModel())
        with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=10)):
            response = self.client.post("/api/inference/private", json={"message": "hello"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["model_connected"])


if __name__ == "__main__":
    unittest.main()
