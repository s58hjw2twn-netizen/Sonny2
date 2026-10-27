import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.customer_proof_flow import prepare_customer_proof, customer_approval_status


class CustomerProofFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.master = root / "master.png"
        self.proof = root / "proof.jpg"
        cv2.imwrite(str(self.master), np.full((700, 900, 3), 110, dtype=np.uint8))

    def test_proof_requires_customer_approval(self):
        record = prepare_customer_proof("job-001", str(self.master), str(self.proof))
        self.assertEqual(record.status, "awaiting_customer_approval")
        self.assertTrue(self.proof.exists())
        self.assertNotEqual(self.proof.read_bytes(), self.master.read_bytes())

    def test_approval_does_not_release_master(self):
        record = prepare_customer_proof("job-001", str(self.master), str(self.proof))
        self.assertEqual(customer_approval_status(record, True),
                         "approved_pending_release_checks")

    def test_rejection_requests_revision(self):
        record = prepare_customer_proof("job-001", str(self.master), str(self.proof))
        self.assertEqual(customer_approval_status(record, False), "revision_requested")

    def test_blank_job_id_denied(self):
        with self.assertRaises(ValueError):
            prepare_customer_proof(" ", str(self.master), str(self.proof))
        self.assertFalse(self.proof.exists())


if __name__ == "__main__":
    unittest.main()
