import unittest
from sonny_vision.quality.benchmark_summary import benchmark_summary

class BenchmarkSummaryTests(unittest.TestCase):
    def test_totals(self):
        result=benchmark_summary()
        self.assertEqual(result["synthetic_total"],10)
        self.assertEqual(result["synthetic_correct"]+len(result["photometric_failures"]),10)
        self.assertGreaterEqual(result["synthetic_accuracy"],0)
        self.assertLessEqual(result["synthetic_accuracy"],1)
    def test_no_real_photo_claims(self):
        result=benchmark_summary()
        self.assertEqual(result["real_photo_samples"],0)
        self.assertIsNone(result["real_photo_accuracy"])
        self.assertFalse(result["identity_preservation_verified"])
        self.assertFalse(result["commercial_readiness"])
