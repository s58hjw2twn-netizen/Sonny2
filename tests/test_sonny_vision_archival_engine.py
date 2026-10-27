import unittest
import numpy as np
from sonny_vision.archival_engine import analyze, restore_archival, quality_gate


class ArchivalEngineTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(7)
        self.source = rng.integers(35, 220, size=(96, 96, 3), dtype=np.uint8)

    def test_deterministic_and_source_immutable(self):
        before = self.source.copy()
        a = restore_archival(self.source)
        b = restore_archival(self.source)
        np.testing.assert_array_equal(a, b)
        np.testing.assert_array_equal(self.source, before)
        self.assertEqual(a.shape, before.shape)

    def test_analysis_has_finite_metrics(self):
        result = analyze(self.source)
        self.assertTrue(np.isfinite(result.blur_variance))
        self.assertTrue(np.isfinite(result.noise_estimate))

    def test_missing_mask_fails_closed(self):
        result = quality_gate(self.source, self.source.copy())
        self.assertFalse(result["passed"])
        self.assertFalse(result["release_allowed"])

    def test_empty_mask_fails_closed(self):
        mask = np.zeros((96, 96), dtype=bool)
        result = quality_gate(self.source, self.source.copy(), mask)
        self.assertFalse(result["passed"])

    def test_protected_change_rejected(self):
        changed = self.source.copy()
        changed[20:40, 20:40] = 255
        mask = np.zeros((96, 96), dtype=bool)
        mask[20:40, 20:40] = True
        result = quality_gate(self.source, changed, mask)
        self.assertFalse(result["passed"])

    def test_even_pass_does_not_authorize_release(self):
        mask = np.ones((96, 96), dtype=bool)
        result = quality_gate(self.source, self.source.copy(), mask)
        self.assertTrue(result["passed"])
        self.assertFalse(result["identity_verified"])
        self.assertFalse(result["release_allowed"])


if __name__ == "__main__":
    unittest.main()
