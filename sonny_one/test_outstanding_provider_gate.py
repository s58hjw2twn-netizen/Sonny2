"""Deterministic tests for orphaned worker admission control."""
import asyncio
from threading import Event
import unittest

from sonny_one.inference import InferenceFailure, InferenceTimeout, Response
from sonny_one.outstanding_provider_gate import OutstandingProviderGate


class BlockingProvider:
    def __init__(self):
        self.started = Event()
        self.release = Event()

    def generate(self, request):
        self.started.set()
        self.release.wait(3)
        return Response(text="finished", model_id="mock", demo=False)


class OutstandingGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_timeout_does_not_free_worker_slot(self):
        gate = OutstandingProviderGate(capacity=1)
        provider = BlockingProvider()
        try:
            with self.assertRaises(InferenceTimeout):
                await gate.run(provider, "hello", timeout_seconds=0.05)
            self.assertTrue(provider.started.is_set())
            with self.assertRaises(InferenceFailure):
                await gate.run(provider, "second", timeout_seconds=0.05)
            provider.release.set()
            for _ in range(50):
                await asyncio.sleep(0.01)
                try:
                    result = await gate.run(provider, "third", timeout_seconds=0.2)
                    self.assertEqual(result.text, "finished")
                    break
                except InferenceFailure:
                    continue
            else:
                self.fail("Worker slot not released")
        finally:
            provider.release.set()
            gate.shutdown()

    async def test_reject_invalid_capacity(self):
        for capacity in (0, True, 65):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                OutstandingProviderGate(capacity)


if __name__ == "__main__":
    unittest.main()
