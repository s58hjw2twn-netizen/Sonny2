"""Regression checks for the isolated local inference endpoint."""
import unittest
import os
from sonny.auth import create_access_token
from unittest.mock import patch

from sonny_one.inference import InferenceFailure, InferenceTimeout

from fastapi.testclient import TestClient
from sonny_one.web_app import app


class InferenceRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_demo_endpoint(self):
        response = self.client.post("/api/inference/demo", json={"message": "hello"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "deterministic-demo")
        self.assertEqual(body["model_id"], "offline-demo-v1")
        self.assertFalse(body["model_connected"])
        self.assertIn("No language model", body["text"])

    def test_provider_failure_returns_503(self):
        async def broken(*args, **kwargs):
            raise InferenceFailure("private internal detail")
        with patch("sonny_one.web_app.generate_with_deadline", side_effect=broken):
            response = self.client.post("/api/inference/demo", json={"message": "hello"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Inference unavailable")
        self.assertNotIn("private", response.text)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")

    def test_provider_timeout_returns_504(self):
        async def slow(*args, **kwargs):
            raise InferenceTimeout("private internal detail")
        with patch("sonny_one.web_app.generate_with_deadline", side_effect=slow):
            response = self.client.post("/api/inference/demo", json={"message": "hello"})
        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["detail"], "Inference timed out")
        self.assertNotIn("private", response.text)

    def test_private_route_requires_authentication(self):
        response = self.client.post("/api/inference/private", json={"message": "hello"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required")

    def test_private_route_rejects_invalid_token(self):
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            response = self.client.post("/api/inference/private", json={"message": "hello"},
                                        headers={"Authorization": "Bearer invalid.token"})
        self.assertEqual(response.status_code, 401)

    def test_private_route_accepts_valid_token(self):
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            token = create_access_token("local-test-user")
            response = self.client.post("/api/inference/private", json={"message": "hello"},
                                        headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["model_connected"])

    def test_private_route_rate_limited(self):
        from sonny_one.rate_limit import LocalRateLimiter
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            token = create_access_token("rate-limit-test-user")
            headers = {"Authorization": "Bearer " + token}
            with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=1)):
                first = self.client.post("/api/inference/private", json={"message": "hello"}, headers=headers)
                second = self.client.post("/api/inference/private", json={"message": "hello"}, headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.headers["Retry-After"], "60")

    def test_private_route_does_not_accept_basic_auth(self):
        response = self.client.post("/api/inference/private", json={"message": "hello"},
                                    headers={"Authorization": "Basic abc"})
        self.assertEqual(response.status_code, 401)

    def test_private_route_wrong_signature_rejected(self):
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "issuer-secret"}):
            token = create_access_token("signature-test-user")
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "verifier-secret"}):
            response = self.client.post("/api/inference/private", json={"message": "hello"},
                                        headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 401)

    def test_private_route_missing_secret_fails_closed(self):
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "issuer-secret"}):
            token = create_access_token("secret-test-user")
        env = {key: value for key, value in os.environ.items() if key != "SONNY_AUTH_SECRET"}
        with patch.dict(os.environ, env, clear=True):
            response = self.client.post("/api/inference/private", json={"message": "hello"},
                                        headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Authentication unavailable")

    def test_unauthenticated_request_never_calls_provider(self):
        with patch("sonny_one.web_app.generate_with_deadline") as provider:
            response = self.client.post("/api/inference/private", json={"message": "hello"})
        self.assertEqual(response.status_code, 401)
        provider.assert_not_called()

    def test_throttled_request_never_calls_provider(self):
        from sonny_one.rate_limit import LocalRateLimiter
        limiter = LocalRateLimiter(limit=1)
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            token = create_access_token("throttled-provider-test")
            headers = {"Authorization": "Bearer " + token}
            with patch("sonny_one.web_app.private_limiter", limiter):
                self.assertEqual(self.client.post("/api/inference/private", json={"message": "hello"},
                                                  headers=headers).status_code, 200)
                with patch("sonny_one.web_app.generate_with_deadline") as provider:
                    response = self.client.post("/api/inference/private",
                                                json={"message": "hello"}, headers=headers)
        self.assertEqual(response.status_code, 429)
        provider.assert_not_called()

    def test_private_limiter_isolates_users(self):
        from sonny_one.rate_limit import LocalRateLimiter
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            alice = {"Authorization": "Bearer " + create_access_token("isolated-alice")}
            bob = {"Authorization": "Bearer " + create_access_token("isolated-bob")}
            with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=1)):
                first = self.client.post("/api/inference/private", json={"message": "hello"}, headers=alice)
                second = self.client.post("/api/inference/private", json={"message": "hello"}, headers=alice)
                third = self.client.post("/api/inference/private", json={"message": "hello"}, headers=bob)
        self.assertEqual([first.status_code, second.status_code, third.status_code], [200, 429, 200])

    def test_private_route_concurrency_capacity(self):
        from sonny_one.concurrency_gate import LocalConcurrencyGate
        gate = LocalConcurrencyGate(max_active=1)
        self.assertTrue(gate.acquire())
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            token = create_access_token("capacity-test-user")
            with patch("sonny_one.web_app.private_concurrency", gate):
                with patch("sonny_one.web_app.generate_with_deadline") as provider:
                    response = self.client.post("/api/inference/private",
                                                json={"message": "hello"},
                                                headers={"Authorization": "Bearer " + token})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Inference capacity reached")
        provider.assert_not_called()
        gate.release()

    def test_empty_message_rejected(self):
        response = self.client.post("/api/inference/demo", json={"message": "  "})
        self.assertEqual(response.status_code, 422)

    def test_long_message_rejected(self):
        response = self.client.post("/api/inference/demo", json={"message": "x" * 4001})
        self.assertEqual(response.status_code, 422)

    def test_legacy_chat_route_preserved(self):
        response = self.client.post("/api/chat", json={"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["mode"], "deterministic-demo")

    def test_security_headers_preserved(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")
        self.assertEqual(response.headers.get("Referrer-Policy"), "no-referrer")
        self.assertIn("microphone=()", response.headers.get("Permissions-Policy", ""))


if __name__ == "__main__":
    unittest.main()
