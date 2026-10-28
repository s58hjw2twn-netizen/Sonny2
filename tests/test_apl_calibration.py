"""Only completed non-infrastructure APL evaluations may enter calibration."""
import unittest
from sonny_one.apl.calibration import prediction_calibration


def record(candidate="a", prediction=0.8, code=0):
    suites = {k: {"exit_code": code} for k in
              ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout")}
    return {"candidate_id": candidate, "predicted_pass": prediction,
            "report": {"candidate_id": candidate, **suites,
                       "status": "ELIGIBLE_FOR_HUMAN_REVIEW" if code == 0 else "REJECTED"}}


class CalibrationTests(unittest.TestCase):
    def test_seedless_deterministic_summary(self):
        result = prediction_calibration([record("a", .8, 0), record("b", .2, 1)])
        self.assertAlmostEqual(result["brier_score"], .04)
        self.assertAlmostEqual(result["mean_prediction_bias"], 0)
        self.assertFalse(result["improvement_proven"])

    def test_missing_or_skipped_results_rejected(self):
        for field in ("heldout", "deterministic"):
            r = record()
            del r["report"][field]
            with self.assertRaises(ValueError):
                prediction_calibration([r])
        r = record()
        r["report"]["heldout"]["skipped"] = True
        with self.assertRaises(ValueError):
            prediction_calibration([r])

    def test_mismatch_duplicate_and_invalid_probabilities(self):
        r = record()
        for bad in (-1, 2, True, float("nan")):
            r["predicted_pass"] = bad
            with self.assertRaises(ValueError):
                prediction_calibration([r])
        with self.assertRaises(ValueError):
            prediction_calibration([record(), record()])
        r = record()
        r["report"]["candidate_id"] = "other"
        with self.assertRaises(ValueError):
            prediction_calibration([r])

    def test_infrastructure_error_cannot_be_counted_as_failure(self):
        r = record(code=1)
        r["report"]["heldout"]["exit_code"] = 125
        with self.assertRaises(ValueError):
            prediction_calibration([r])
        r = record()
        r["report"]["status"] = "REJECTED"
        with self.assertRaises(ValueError):
            prediction_calibration([r])


class QueueCalibrationTests(unittest.TestCase):
    def test_complete_queue_can_be_calibrated(self):
        from sonny_one.apl.calibration import calibrate_queue
        patch_text = ("diff --git a/sonny_one/apl_targets/x.py b/sonny_one/apl_targets/x.py\n"
                      "--- a/sonny_one/apl_targets/x.py\n"
                      "+++ b/sonny_one/apl_targets/x.py\n"
                      "@@ -1 +1 @@\n-old\n+new\n")
        from sonny_one.apl.policy import sha256_bytes
        cid = sha256_bytes(patch_text.encode())
        example = record(cid, .8, 0)
        result = calibrate_queue([{"patch_text": patch_text, "predicted_pass": .8}],
                                 {"attempted": 1, "reports": [example["report"]],
                                  "promotion": "FORBIDDEN", "improvement_proven": False})
        self.assertAlmostEqual(result["brier_score"], .04)

    def test_queue_rejects_unmatched_or_incomplete_evidence(self):
        from sonny_one.apl.calibration import calibrate_queue
        proposal = {"patch_text": "not a patch", "predicted_pass": .9}
        with self.assertRaises(ValueError):
            calibrate_queue([proposal], {"attempted": 0, "reports": [],
                                         "promotion": "FORBIDDEN", "improvement_proven": False})
