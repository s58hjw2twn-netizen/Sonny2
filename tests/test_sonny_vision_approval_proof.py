import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.approval_proof import make_approval_proof, write_approval_proof


class ApprovalProofTests(unittest.TestCase):
    def setUp(self):
        self.image = np.full((1800, 1200, 3), 125, dtype=np.uint8)

    def test_proof_reduced_and_visibly_modified(self):
        proof = cv2.imdecode(np.frombuffer(make_approval_proof(self.image), dtype=np.uint8),
                             cv2.IMREAD_COLOR)
        self.assertLessEqual(max(proof.shape[:2]), 1200)
        self.assertGreater(float(proof.std()), 3.0)

    def test_original_immutable(self):
        before = self.image.copy()
        make_approval_proof(self.image)
        np.testing.assert_array_equal(before, self.image)

    def test_invalid_size_denied(self):
        with self.assertRaises(ValueError):
            make_approval_proof(self.image, max_edge=200)

    def test_master_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            master = Path(d) / "master.png"
            cv2.imwrite(str(master), self.image)
            before = master.read_bytes()
            with self.assertRaises(ValueError):
                write_approval_proof(str(master), str(master))
            self.assertEqual(before, master.read_bytes())

    def test_existing_preview_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            master, preview = Path(d) / "master.png", Path(d) / "preview.jpg"
            cv2.imwrite(str(master), self.image)
            preview.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                write_approval_proof(str(master), str(preview))
            self.assertEqual(preview.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
