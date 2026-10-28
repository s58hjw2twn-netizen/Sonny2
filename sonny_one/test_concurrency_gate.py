"""Local concurrency admission tests; no external inference service."""
import unittest
from sonny_one.concurrency_gate import LocalConcurrencyGate


class ConcurrencyGateTests(unittest.TestCase):
    def test_capacity_and_release(self):
        gate = LocalConcurrencyGate(max_active=2)
        self.assertTrue(gate.acquire())
        self.assertTrue(gate.acquire())
        self.assertFalse(gate.acquire())
        gate.release()
        self.assertTrue(gate.acquire())

    def test_invalid_capacity(self):
        for capacity in (0, -1, True, 129, "4"):
            with self.subTest(capacity=capacity), self.assertRaises(ValueError):
                LocalConcurrencyGate(max_active=capacity)

    def test_overrelease_rejected(self):
        gate = LocalConcurrencyGate(max_active=1)
        with self.assertRaises(ValueError):
            gate.release()


if __name__ == "__main__":
    unittest.main()
