import hashlib
import tempfile
import unittest
from pathlib import Path
from sonny_vision.review_gate_v17 import sign_decision
from sonny_vision.release_export import export_reviewed


class ReleaseExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.candidate, self.destination = (root / n for n in ("source.bin", "candidate.bin", "delivery.bin"))
        self.source.write_bytes(b"original")
        self.candidate.write_bytes(b"candidate")
        self.secret = b"z" * 32

    def decision(self):
        return sign_decision(hashlib.sha256(self.source.read_bytes()).hexdigest(),
                             hashlib.sha256(self.candidate.read_bytes()).hexdigest(),
                             "operator", "customer_release", True, self.secret)

    def export(self, decision, quality=True, identity=True):
        return export_reviewed(str(self.source), str(self.candidate), str(self.destination),
                               decision, self.secret, quality, identity)

    def test_unapproved_not_written(self):
        self.assertFalse(self.export(None))
        self.assertFalse(self.destination.exists())

    def test_changed_candidate_not_written(self):
        decision = self.decision()
        self.candidate.write_bytes(b"altered")
        self.assertFalse(self.export(decision))
        self.assertFalse(self.destination.exists())

    def test_missing_review_not_written(self):
        self.assertFalse(self.export(self.decision(), identity=False))
        self.assertFalse(self.destination.exists())

    def test_valid_release_exact_bytes(self):
        self.assertTrue(self.export(self.decision()))
        self.assertEqual(self.destination.read_bytes(), self.candidate.read_bytes())

    def test_existing_destination_never_overwritten(self):
        self.destination.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            self.export(self.decision())
        self.assertEqual(self.destination.read_bytes(), b"existing")

    def test_symlink_destination_rejected(self):
        target = Path(self.tmp.name) / "target.bin"
        target.write_bytes(b"safe")
        self.destination.symlink_to(target)
        with self.assertRaises(ValueError):
            self.export(self.decision())
        self.assertEqual(target.read_bytes(), b"safe")


if __name__ == "__main__":
    unittest.main()
