import asyncio
import json
import unittest

from sonny_one.integration.status_asgi import app


def request(method, path):
    sent = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app({"type": "http", "method": method, "path": path}, receive, send))
    return sent[0]["status"], json.loads(sent[1]["body"])


class StatusAsgiTests(unittest.TestCase):
    def test_public_status_remains_disabled(self):
        status, payload = request("GET", "/v1/public/status")
        self.assertEqual(status, 200)
        self.assertFalse(payload["runtime_connected"])
        self.assertFalse(payload["unattended_development_enabled"])
        self.assertEqual(payload["enabled_capabilities"], [])

    def test_health_does_not_claim_connected(self):
        status, payload = request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["service"], "sonny-one-bridge")
        self.assertNotIn("runtime_connected", payload)

    def test_mutations_and_private_routes_not_available(self):
        for method, path in [
            ("POST", "/v1/public/status"),
            ("GET", "/v1/private/memory"),
            ("POST", "/v1/development/commit"),
            ("POST", "/v1/development/execute"),
        ]:
            with self.subTest(method=method, path=path):
                self.assertEqual(request(method, path)[0], 404)


if __name__ == "__main__":
    unittest.main()
