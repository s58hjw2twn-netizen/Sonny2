import tempfile
import unittest
from pathlib import Path
from hashlib import sha256
import numpy as np
from PIL import Image
from sonny_vision.precision_pipeline import prepare_case, approve_case
from sonny_vision.precision_release_gate import ReleaseDenied
from sonny_vision.assurance import FailureLedger

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        self.replacement = self.root / "replacement.png"
        self.mask = self.root / "mask.png"
        source = np.zeros((100,100,3), dtype=np.uint8)
        replacement = source.copy()
        replacement[45:48,45:48] = [220,160,30]
        mask = np.zeros((100,100), dtype=np.uint8)
        mask[40:50,40:50] = 255
        Image.fromarray(source).save(self.source)
        Image.fromarray(replacement).save(self.replacement)
        Image.fromarray(mask).save(self.mask)

    def prepare(self, **changes):
        args = dict(source=self.source,replacement=self.replacement,mask=self.mask,
                    workspace=self.root / "cases",case_id="case1",
                    reference_id="reference-001",reference_verified=True,
                    mask_approved=True,independent_review="review-001")
        return prepare_case(**(args | changes))

    def test_preview_and_approval_are_separate(self):
        result = self.prepare()
        case = Path(result["case_dir"])
        self.assertTrue((case / "review_preview.png").exists())
        self.assertFalse((case / "approval.json").exists())
        self.assertEqual(result["verification"]["outside_mask_changes"],0)
        digest = sha256((case / "candidate.png").read_bytes()).hexdigest()
        approved = approve_case(case,expected_candidate_sha256=digest,
                                customer_approval_token="explicit-approval")
        self.assertEqual(approved["status"],"approved_for_release")

    def test_wrong_hash_denied(self):
        case = Path(self.prepare()["case_dir"])
        with self.assertRaises(ReleaseDenied):
            approve_case(case,expected_candidate_sha256="bad",
                         customer_approval_token="yes")

    def test_no_approval_denied(self):
        case = Path(self.prepare()["case_dir"])
        digest = sha256((case / "candidate.png").read_bytes()).hexdigest()
        with self.assertRaises(ReleaseDenied):
            approve_case(case,expected_candidate_sha256=digest,
                         customer_approval_token="")

    def test_missing_reference_denied_before_edit(self):
        with self.assertRaises(ReleaseDenied):
            self.prepare(reference_verified=False)
        self.assertFalse((self.root / "cases" / "case1").exists())

    def test_duplicate_case_denied(self):
        self.prepare()
        with self.assertRaises(ReleaseDenied):
            self.prepare()

    def test_repeated_failed_method_blocked_before_case_creation(self):
        ledger = FailureLedger(self.root / "failures.jsonl")
        for index in range(2):
            ledger.record(task_type="precision_image_edit",
                          method="pixel_locked_composite",
                          failure_code="invalid_output",
                          evidence_ref=f"case-{index}")
        with self.assertRaisesRegex(ReleaseDenied, "repeated_failure"):
            self.prepare(failure_ledger=ledger)
        self.assertFalse((self.root / "cases" / "case1").exists())

    def test_single_failure_does_not_trigger_threshold(self):
        ledger = FailureLedger(self.root / "failures.jsonl")
        ledger.record(task_type="precision_image_edit",
                      method="pixel_locked_composite",
                      failure_code="invalid_output", evidence_ref="case-0")
        result = self.prepare(failure_ledger=ledger)
        self.assertEqual(result["verification"]["outside_mask_changes"], 0)

    def test_outside_mask_candidate_is_restricted(self):
        candidate = np.asarray(Image.open(self.replacement)).copy()
        candidate[0,0] = [255,255,255]
        Image.fromarray(candidate).save(self.replacement)
        result = self.prepare()
        self.assertEqual(result["verification"]["outside_mask_changes"],0)

if __name__ == "__main__":
    unittest.main()
