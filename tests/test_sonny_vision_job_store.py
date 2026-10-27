import hashlib
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.approval_proof import write_approval_proof
from sonny_vision.proof_access import issue_proof_token
from sonny_vision.job_store import (initialize_jobs, create_job,
                                    get_customer_job, record_customer_decision)
from sonny_vision.job_proof_service import serve_customer_job_proof


class JobStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.db = str(root / "jobs.sqlite")
        initialize_jobs(self.db)
        master = root / "master.png"
        self.proof = root / "proof.jpg"
        cv2.imwrite(str(master), np.full((500, 700, 3), 110, dtype=np.uint8))
        write_approval_proof(str(master), str(self.proof))
        self.digest = hashlib.sha256(self.proof.read_bytes()).hexdigest()
        create_job(self.db, "job", "owner", self.digest)
        self.secret = b"k" * 32
        self.token = issue_proof_token("job", "owner", self.digest,
                                       self.secret, now=100)

    def serve(self, customer="owner"):
        return serve_customer_job_proof(
            database_path=self.db, proof_path=str(self.proof), job_id="job",
            authenticated_customer_id=customer, token=self.token,
            secret=self.secret, now=200)

    def test_valid_owner_receives_proof(self):
        self.assertEqual(self.serve().status, 200)

    def test_other_customer_denied(self):
        self.assertIsNone(get_customer_job(self.db, "job", "intruder"))
        self.assertEqual(self.serve("intruder").status, 403)

    def test_approval_revokes_proof(self):
        self.assertTrue(record_customer_decision(self.db, "job", "owner", True))
        self.assertEqual(self.serve().status, 403)

    def test_revision_revokes_proof(self):
        self.assertTrue(record_customer_decision(self.db, "job", "owner", False))
        self.assertEqual(self.serve().status, 403)

    def test_second_decision_denied(self):
        self.assertTrue(record_customer_decision(self.db, "job", "owner", True))
        self.assertFalse(record_customer_decision(self.db, "job", "owner", False))

    def test_wrong_customer_cannot_approve(self):
        self.assertFalse(record_customer_decision(self.db, "job", "intruder", True))
        self.assertEqual(get_customer_job(self.db, "job", "owner")[0],
                         "awaiting_customer_approval")

    def test_duplicate_job_denied(self):
        with self.assertRaises(Exception):
            create_job(self.db, "job", "owner", self.digest)


if __name__ == "__main__":
    unittest.main()
