"""Unit tests for global budget enforcement at the private HTTP boundary."""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sonny.auth import create_access_token
from sonny_one.global_quota import GlobalRequestQuota
from sonny_one.rate_limit import LocalRateLimiter
from sonny_one.web_app import app


class GlobalQuotaRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_budget_exhaustion_never_calls_provider(self):
        with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
            token = create_access_token("global-budget-user")
            headers = {"Authorization": "Bearer " + token}
            with patch("sonny_one.web_app.private_global_quota", GlobalRequestQuota(1)):
                with patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=10)):
                    first = self.client.post("/api/inference/private", json={"message": "hello"}, headers=headers)
                    with patch("sonny_one.web_app.generate_with_deadline") as provider:
                        second = self.client.post("/api/inference/private", json={"message": "hello"}, headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["detail"], "Global inference budget exhausted")
        provider.assert_not_called()

    def test_unauthenticated_request_does_not_spend_budget(self):
        quota = GlobalRequestQuota(1)
        with patch("sonny_one.web_app.private_global_quota", quota):
            response = self.client.post("/api/inference/private", json={"message": "hello"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(quota.remaining, 1)


if __name__ == "__main__":
    unittest.main()
