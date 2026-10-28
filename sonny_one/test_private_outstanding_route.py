"""Route-level regression tests for bounded outstanding provider work."""
import os
import unittest
from threading import Event
from unittest.mock import patch

from fastapi.testclient import TestClient

from sonny.auth import create_access_token
from sonny_one.inference import Response
from sonny_one.outstanding_provider_gate import OutstandingProviderGate
from sonny_one.private_provider import install_private_provider, reset_private_provider
from sonny_one.rate_limit import LocalRateLimiter
from sonny_one.global_quota import GlobalRequestQuota
from sonny_one.web_app import app


class SlowProvider:
    def __init__(self):
        self.started = Event()
        self.release = Event()

    def generate(self, request):
        self.started.set()
        self.release.wait(3)
        return Response("done", "slow-mock", demo=False)


class PrivateGateRouteTests(unittest.TestCase):
    def test_busy_worker_rejects_second_request(self):
        provider = SlowProvider()
        gate = OutstandingProviderGate(capacity=1)
        try:
            with patch.dict(os.environ, {"SONNY_AUTH_SECRET": "test-only-secret"}):
                token = create_access_token("gate-user")
                headers = {"Authorization": "Bearer " + token}
                install_private_provider(provider, approved=True)
                with patch("sonny_one.web_app.private_provider_gate", gate), \
                     patch("sonny_one.web_app.private_limiter", LocalRateLimiter(limit=10)), \
                     patch("sonny_one.web_app.private_global_quota", GlobalRequestQuota(10)):
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                        first = pool.submit(TestClient(app).post, "/api/inference/private",
                                            json={"message": "first"}, headers=headers)
                        self.assertTrue(provider.started.wait(2))
                        second = TestClient(app).post("/api/inference/private",
                                                       json={"message": "second"}, headers=headers)
                        provider.release.set()
                        first_result = first.result(timeout=4)
                    self.assertEqual(second.status_code, 503)
                    self.assertEqual(second.json()["detail"], "Inference unavailable")
                    self.assertEqual(first_result.status_code, 200)
        finally:
            provider.release.set()
            reset_private_provider()
            gate.shutdown()


if __name__ == "__main__":
    unittest.main()
