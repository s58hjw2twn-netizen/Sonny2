"""Deterministic no-network tests for the opt-in local benchmark runner."""
import unittest

from sonny_one.inference import OfflineProvider, Response
from sonny_one.local_benchmark_runner import BenchmarkCase, run_local_benchmark


class FakeProvider:
    def __init__(self, model_id="test-model"):
        self.model_id = model_id
        self.prompts = []

    def generate(self, request):
        self.prompts.append(request.prompt)
        return Response("42", self.model_id, demo=False)


class LocalBenchmarkRunnerTests(unittest.TestCase):
    def test_collects_repeated_trials(self):
        provider = FakeProvider()
        ticks = iter([1, 1.01, 2, 2.02, 3, 3.03, 4, 4.04])
        trials, report = run_local_benchmark(
            provider, "test-model",
            [BenchmarkCase("a", "What is 6 times 7?", "42"),
             BenchmarkCase("b", "Reply 42", "42")],
            repetitions=2, clock=lambda: next(ticks),
        )
        self.assertEqual(len(trials), 4)
        self.assertEqual(report["exact_match_rate"], 1.0)
        self.assertEqual(report["trials"], 4)
        self.assertEqual(provider.prompts, ["What is 6 times 7?", "Reply 42"] * 2)

    def test_rejects_demo_response(self):
        with self.assertRaises(ValueError):
            run_local_benchmark(OfflineProvider(), "offline-demo-v1",
                                [BenchmarkCase("a", "hello", "hello")])

    def test_rejects_model_mismatch(self):
        with self.assertRaises(ValueError):
            run_local_benchmark(FakeProvider("wrong"), "expected",
                                [BenchmarkCase("a", "hello", "42")])

    def test_rejects_duplicate_tasks(self):
        with self.assertRaises(ValueError):
            run_local_benchmark(FakeProvider(), "test-model",
                                [BenchmarkCase("a", "one", "1"),
                                 BenchmarkCase("a", "two", "2")])

    def test_rejects_unbounded_runs(self):
        with self.assertRaises(ValueError):
            run_local_benchmark(FakeProvider(), "test-model",
                                [BenchmarkCase("a", "one", "1")], repetitions=6)


if __name__ == "__main__":
    unittest.main()
