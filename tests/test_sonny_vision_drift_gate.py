import unittest
from sonny_vision.identity.drift_gate import drift_report

FACE = {"left_eye":(.3,.3), "right_eye":(.7,.3), "nose":(.5,.5),
        "mouth_left":(.4,.7), "mouth_right":(.6,.7), "chin":(.5,.9)}

class DriftTests(unittest.TestCase):
    def test_identical(self):
        r = drift_report([FACE, FACE, FACE])
        self.assertTrue(r["geometry_pass"])
        self.assertFalse(r["identity_verified"])

    def test_cumulative_drift(self):
        stages = [FACE] + [dict(FACE, nose=(.5+d,.5)) for d in (.01,.02,.04)]
        self.assertFalse(drift_report(stages)["geometry_pass"])

    def test_missing_landmarks(self):
        with self.assertRaises(ValueError):
            drift_report([FACE, {}])

    def test_nonfinite_coordinates(self):
        with self.assertRaises(ValueError):
            drift_report([FACE, dict(FACE, nose=(float("nan"),.5))])

    def test_missing_stage(self):
        with self.assertRaises(ValueError):
            drift_report([FACE])
