"""Tests for local global inference request budget."""
import unittest
from concurrent.futures import ThreadPoolExecutor
from sonny_one.global_quota import GlobalRequestQuota


class GlobalQuotaTests(unittest.TestCase):
    def test_exhaustion(self):
        quota = GlobalRequestQuota(2)
        self.assertTrue(quota.allow())
        self.assertTrue(quota.allow())
        self.assertFalse(quota.allow())
        self.assertEqual(quota.remaining, 0)

    def test_concurrent_atomic_budget(self):
        quota = GlobalRequestQuota(5)
        with ThreadPoolExecutor(max_workers=20) as pool:
            outcomes = list(pool.map(lambda _: quota.allow(), range(100)))
        self.assertEqual(sum(outcomes), 5)
        self.assertEqual(quota.remaining, 0)

    def test_invalid_limits(self):
        for value in (0, 10001, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                GlobalRequestQuota(value)


if __name__ == "__main__":
    unittest.main()
