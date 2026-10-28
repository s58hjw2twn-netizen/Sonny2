"""Local rate limiter tests; no clocks or network services needed."""
import unittest
from unittest.mock import patch
from sonny_one.rate_limit import LocalRateLimiter


class RateLimiterTests(unittest.TestCase):
    def test_limit_per_identity(self):
        limiter = LocalRateLimiter(limit=2, window_seconds=60)
        with patch("sonny_one.rate_limit.monotonic", return_value=100):
            self.assertTrue(limiter.allow("alice"))
            self.assertTrue(limiter.allow("alice"))
            self.assertFalse(limiter.allow("alice"))
            self.assertTrue(limiter.allow("bob"))

    def test_window_expiration(self):
        limiter = LocalRateLimiter(limit=1, window_seconds=10)
        with patch("sonny_one.rate_limit.monotonic", return_value=100):
            self.assertTrue(limiter.allow("alice"))
        with patch("sonny_one.rate_limit.monotonic", return_value=111):
            self.assertTrue(limiter.allow("alice"))

    def test_capacity_rejects_new_identities(self):
        limiter = LocalRateLimiter(limit=1, window_seconds=60, max_identities=1)
        with patch("sonny_one.rate_limit.monotonic", return_value=100):
            self.assertTrue(limiter.allow("alice"))
            self.assertFalse(limiter.allow("bob"))

    def test_expired_identity_is_evicted(self):
        limiter = LocalRateLimiter(limit=1, window_seconds=10, max_identities=1)
        with patch("sonny_one.rate_limit.monotonic", return_value=100):
            self.assertTrue(limiter.allow("alice"))
        with patch("sonny_one.rate_limit.monotonic", return_value=111):
            self.assertTrue(limiter.allow("bob"))

    def test_nonfinite_window_rejected(self):
        with self.assertRaises(ValueError):
            LocalRateLimiter(window_seconds=float("nan"))

    def test_invalid_identity_rejected(self):
        self.assertFalse(LocalRateLimiter().allow(""))

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            LocalRateLimiter(limit=0)


if __name__ == "__main__":
    unittest.main()
