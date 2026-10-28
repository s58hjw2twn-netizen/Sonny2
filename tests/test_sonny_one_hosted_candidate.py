import asyncio
import unittest
from sonny_one.hosted_candidate import build_hosted_candidate
from sonny_one.hosted_config import HostedConfig

def request(app, headers=None):
    messages = []
    async def send(message):
        messages.append(message)
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    asyncio.run(app({"type": "http", "method": "GET",
                     "headers": headers or [(b"host", b"sonny.example")]},
                    receive, send))
    return messages[0]["status"]

class HostedCandidateTests(unittest.TestCase):
    def setUp(self):
        self.config = HostedConfig("https://sonny.example",
                                   "configured-persistent-database",
                                   "s" * 48)

    def test_default_denies_without_verified_tls(self):
        self.assertEqual(request(build_hosted_candidate(self.config)), 403)

    def test_verified_tls_still_not_live(self):
        self.assertEqual(request(build_hosted_candidate(
            self.config, trusted_tls=True)), 503)

    def test_invalid_configuration_rejected(self):
        with self.assertRaises(ValueError):
            build_hosted_candidate(HostedConfig("http://sonny.example",
                                                "db", "s" * 48))

    def test_wrong_host_denied(self):
        app = build_hosted_candidate(self.config, trusted_tls=True)
        self.assertEqual(request(app, [(b"host", b"untrusted.example")]), 403)

if __name__ == "__main__":
    unittest.main()
