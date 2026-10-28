import asyncio
import unittest
from sonny_one.hosted_boundary import HostedRequestBoundary

async def allowed_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})

def invoke(*, headers=None, method="GET", tls=True):
    boundary = HostedRequestBoundary(
        allowed_app, canonical_origin="https://sonny.example", verified_tls=tls)
    events = []
    async def send(message):
        events.append(message)
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    asyncio.run(boundary({"type": "http", "method": method,
                          "headers": headers if headers is not None else
                          [(b"host", b"sonny.example")]}, receive, send))
    return events[0]["status"]

class HostedBoundaryTests(unittest.TestCase):
    def test_same_host_get(self):
        self.assertEqual(invoke(), 200)
    def test_same_origin_post(self):
        self.assertEqual(invoke(method="POST", headers=[
            (b"host", b"sonny.example"),
            (b"origin", b"https://sonny.example")]), 200)
    def test_missing_host(self):
        self.assertEqual(invoke(headers=[]), 403)
    def test_duplicate_host(self):
        self.assertEqual(invoke(headers=[
            (b"host", b"sonny.example"), (b"host", b"sonny.example")]), 403)
    def test_wrong_host(self):
        self.assertEqual(invoke(headers=[(b"host", b"other.example")]), 403)
    def test_cross_origin(self):
        self.assertEqual(invoke(headers=[
            (b"host", b"sonny.example"), (b"origin", b"https://evil.example")]), 403)
    def test_missing_origin_on_write(self):
        self.assertEqual(invoke(method="POST"), 403)
    def test_tls_not_verified(self):
        self.assertEqual(invoke(tls=False), 403)

if __name__ == "__main__":
    unittest.main()
