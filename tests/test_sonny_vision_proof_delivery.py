import hashlib
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.approval_proof import write_approval_proof
from sonny_vision.proof_access import issue_proof_token
from sonny_vision.proof_delivery import serve_approval_proof


class ProofDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        master, self.proof = root / "master.png", root / "proof.jpg"
        cv2.imwrite(str(master), np.full((500, 700, 3), 125, dtype=np.uint8))
        write_approval_proof(str(master), str(self.proof))
        self.digest = hashlib.sha256(self.proof.read_bytes()).hexdigest()
        self.key = b"k" * 32
        self.token = issue_proof_token("job", "customer", self.digest,
                                       self.key, now=100, ttl_seconds=300)

    def serve(self, **changes):
        args = dict(proof_path=str(self.proof), job_id="job", customer_id="customer",
                    authenticated_customer_id="customer", token=self.token,
                    expected_proof_sha256=self.digest, secret=self.key, now=200)
        args.update(changes)
        return serve_approval_proof(**args)

    def test_authorized_preview_is_jpeg(self):
        response = self.serve()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, self.proof.read_bytes())
        self.assertEqual(response.headers["Cache-Control"], "no-store, private")

    def test_approved_proof_no_longer_accessible(self):
        self.assertEqual(self.serve(proof_status="approved_pending_release_checks").status, 403)

    def test_revision_requested_proof_no_longer_accessible(self):
        self.assertEqual(self.serve(proof_status="revision_requested").status, 403)

    def test_other_customer_denied(self):
        self.assertEqual(self.serve(authenticated_customer_id="intruder").status, 403)

    def test_expired_token_denied(self):
        self.assertEqual(self.serve(now=400).status, 403)

    def test_wrong_proof_digest_denied(self):
        self.assertEqual(self.serve(expected_proof_sha256="a" * 64).status, 403)

    def test_tampered_proof_denied(self):
        self.proof.write_bytes(b"tampered")
        self.assertEqual(self.serve().status, 403)

    def test_symlink_proof_denied(self):
        original = self.proof.read_bytes()
        target = self.proof.with_name("target.jpg")
        target.write_bytes(original)
        self.proof.unlink()
        self.proof.symlink_to(target)
        self.assertEqual(self.serve().status, 403)

    def test_missing_proof_denied(self):
        self.proof.unlink()
        self.assertEqual(self.serve().status, 403)

    def test_large_proof_denied(self):
        self.assertEqual(self.serve(max_proof_bytes=10).status, 403)


if __name__ == "__main__":
    unittest.main()
