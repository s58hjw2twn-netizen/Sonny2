"""Unit tests for local-model benchmark scoring; no model or network needed."""
import unittest
from sonny_one.local_model_benchmark import Trial, comparable_models, summarize


class BenchmarkTests(unittest.TestCase):
    def test_exact_match_and_latency(self):
        trials = [
            Trial("t1", "small", "Hello world", " hello   WORLD ", 12),
            Trial("t2", "small", "42", "43", 18),
            Trial("t1", "large", "Hello world", "Hello world", 22),
            Trial("t2", "large", "42", "42", 30),
        ]
        self.assertTrue(comparable_models(trials))
        report = summarize(trials)
        self.assertEqual(report["small"]["exact_match_rate"], 0.5)
        self.assertEqual(report["small"]["median_latency_ms"], 15)
        self.assertEqual(report["large"]["exact_match_rate"], 1)
        self.assertEqual(report["large"]["median_latency_ms"], 26)

    def test_incomparable_task_coverage(self):
        trials = [Trial("a", "one", "x", "x", 1),
                  Trial("b", "two", "x", "x", 1)]
        self.assertFalse(comparable_models(trials))

    def test_repetitions_must_match(self):
        trials = [Trial("a", "one", "x", "x", 1),
                  Trial("a", "one", "x", "x", 2),
                  Trial("a", "two", "x", "x", 1)]
        self.assertFalse(comparable_models(trials))

    def test_reject_invalid_values(self):
        for latency in (-1, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                Trial("t", "m", "x", "x", latency)
        with self.assertRaises(ValueError):
            summarize([])
        with self.assertRaises(ValueError):
            Trial("", "m", "x", "x", 1)


if __name__ == "__main__":
    unittest.main()
