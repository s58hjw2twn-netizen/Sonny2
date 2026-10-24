"""Async inference deadline regression tests (no network, no credentials)."""
import asyncio
import unittest

from sonny_one.inference import InferenceTimeout, OfflineProvider, Response
from sonny_one.inference_async import generate_with_deadline


class AsyncInferenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_offline_provider(self):
        result = await generate_with_deadline(OfflineProvider(), "hello")
        self.assertTrue(result.demo)

    async def test_invalid_timeout(self):
        with self.assertRaises(ValueError):
            await generate_with_deadline(OfflineProvider(), "hello", timeout_seconds=float("nan"))

    async def test_budget_reaches_provider(self):
        observed = []
        class Recorder:
            def generate(self, request):
                observed.append(request.timeout_seconds)
                return Response("ok", "fake", False)
        await generate_with_deadline(Recorder(), "hello", timeout_seconds=3.5)
        self.assertEqual(observed, [3.5])

    async def test_provider_timeout(self):
        class Slow:
            def generate(self, request):
                import time
                time.sleep(0.08)
                return Response("too late", "slow", False)
        with self.assertRaisesRegex(InferenceTimeout, "^Inference timed out$"):
            await generate_with_deadline(Slow(), "hello", timeout_seconds=0.01)

    async def test_provider_error(self):
        class Broken:
            def generate(self, request):
                raise RuntimeError("secret")
        with self.assertRaisesRegex(Exception, "^Inference unavailable$"):
            await generate_with_deadline(Broken(), "hello")


if __name__ == "__main__":
    unittest.main()
