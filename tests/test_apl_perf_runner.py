"""No-Docker unit tests for the isolated performance benchmark launcher."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sonny_one.apl.perf_runner import benchmark_in_docker


IMAGE = "python@sha256:" + "a" * 64


def valid_report():
    return {
        "promotion_allowed": False,
        "method": "alternating_wall_clock_ns_prepostcheck",
        "rounds": 12,
        "calls_per_round": 60,
        "shared_runner_noise_uncontrolled": True,
        "independent_external_benchmark_verified": False,
        "baseline_median_ns": 100,
        "candidate_median_ns": 80,
        "candidate_over_baseline_ratio": 0.8,
        "input_shapes": ["descending"],
        "shape_timings": {
            "descending": {
                "baseline_median_ns": 100,
                "candidate_median_ns": 80,
                "candidate_over_baseline_ratio": 0.8,
            },
        },
    }


class TestPerformanceIsolation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.script = Path(self.tmp.name) / "trusted_benchmark.py"
        self.script.write_text("print('test')\n", encoding="utf-8")

    def test_docker_command_enforces_isolation(self):
        observed = []
        def fake_execute(argv, **kwargs):
            observed.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0,
                json.dumps(valid_report()), "")
        with patch("sonny_one.apl.perf_runner.bounded_execute",
                   side_effect=fake_execute):
            result = benchmark_in_docker(IMAGE, "x = 1\n", "x = 2\n",
                                         self.script)
        self.assertEqual(result["rounds"], 12)
        args = observed[0][0]
        for required in ("--network=none", "--cap-drop=ALL",
                         "--security-opt=no-new-privileges", "--read-only",
                         "--user=65534:65534", "--pull=never",
                         "--entrypoint=python", "-I", "-B"):
            self.assertIn(required, args)
        self.assertTrue(any(a.startswith("--volume=") and a.endswith(":/bench:ro")
                            for a in args))

    def test_invalid_image_rejected_before_docker(self):
        with patch("sonny_one.apl.perf_runner.bounded_execute") as execute:
            with self.assertRaises(ValueError):
                benchmark_in_docker("python:latest", "", "", self.script)
            execute.assert_not_called()

    def test_timeout_forces_named_container_cleanup(self):
        calls = []
        def fake_execute(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["docker", "run"]:
                raise subprocess.TimeoutExpired(argv, 1)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("sonny_one.apl.perf_runner.bounded_execute",
                   side_effect=fake_execute):
            with self.assertRaises(RuntimeError):
                benchmark_in_docker(IMAGE, "", "", self.script)
        self.assertEqual(calls[1][:3], ["docker", "rm", "--force"])
        self.assertEqual(calls[1][3], calls[0][calls[0].index(
            next(a for a in calls[0] if a.startswith("--name=")))][7:])

    def test_rejects_forged_or_inconsistent_benchmark_measurements(self):
        mutations = [
            {"candidate_over_baseline_ratio": 0.1},
            {"baseline_median_ns": 0},
            {"candidate_median_ns": float("nan")},
            {"rounds": True},
            {"independent_external_benchmark_verified": True},
            {"shape_timings": {}},
        ]
        for change in mutations:
            with self.subTest(change=change):
                report = valid_report()
                report.update(change)
                with patch("sonny_one.apl.perf_runner.bounded_execute",
                           return_value=subprocess.CompletedProcess(
                               [], 0, json.dumps(report), "")):
                    with self.assertRaises(RuntimeError):
                        benchmark_in_docker(IMAGE, "", "", self.script)

    def test_invalid_benchmark_json_rejected(self):
        with patch("sonny_one.apl.perf_runner.bounded_execute",
                   return_value=subprocess.CompletedProcess([], 0, "{}", "")):
            with self.assertRaises(RuntimeError):
                benchmark_in_docker(IMAGE, "", "", self.script)


if __name__ == "__main__":
    unittest.main()
