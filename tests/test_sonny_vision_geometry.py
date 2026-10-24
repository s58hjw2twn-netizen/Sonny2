import unittest

from sonny_vision.identity.geometry_gate import geometry_report

FACE = {
    "left_eye": (0.3, 0.3), "right_eye": (0.7, 0.3),
    "nose": (0.5, 0.5), "mouth_left": (0.4, 0.7),
    "mouth_right": (0.6, 0.7), "chin": (0.5, 0.9),
}


class GeometryGateTests(unittest.TestCase):
    def test_identical_passes_but_does_not_verify_identity(self):
        report = geometry_report(FACE, FACE)
        self.assertTrue(report["geometry_pass"])
        self.assertFalse(report["identity_verified"])

    def test_moved_eye_rejected(self):
        altered = dict(FACE, left_eye=(0.4, 0.3))
        self.assertFalse(geometry_report(FACE, altered)["geometry_pass"])

    def test_missing_landmark_rejected(self):
        with self.assertRaises(ValueError):
            geometry_report(FACE, {})

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            geometry_report(FACE, dict(FACE, nose=(float("nan"), 0.5)))

    def test_out_of_range_rejected(self):
        with self.assertRaises(ValueError):
            geometry_report(FACE, dict(FACE, chin=(1.2, 0.9)))


if __name__ == "__main__":
    unittest.main()
