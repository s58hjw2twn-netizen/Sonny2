import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np
from sonny_vision.archival_engine import process_file


class ArchivalOutputSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "original.png"
        cv2.imwrite(str(self.source), np.full((48, 48, 3), 110, dtype=np.uint8))
        self.original = self.source.read_bytes()
        self.output = self.root / "restored.png"
        self.audit = self.root / "audit.json"

    def test_original_as_output_rejected(self):
        with self.assertRaises(ValueError):
            process_file(str(self.source), str(self.source), str(self.audit))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_original_as_audit_rejected(self):
        with self.assertRaises(ValueError):
            process_file(str(self.source), str(self.output), str(self.source))
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertFalse(self.output.exists())

    def test_existing_output_rejected(self):
        self.output.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            process_file(str(self.source), str(self.output), str(self.audit))
        self.assertEqual(self.output.read_bytes(), b"existing")

    def test_existing_audit_rejected(self):
        self.audit.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            process_file(str(self.source), str(self.output), str(self.audit))
        self.assertEqual(self.audit.read_bytes(), b"existing")
        self.assertFalse(self.output.exists())

    def test_valid_run_writes_distinct_files(self):
        report = process_file(str(self.source), str(self.output), str(self.audit))
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertTrue(self.output.exists())
        self.assertTrue(self.audit.exists())
        self.assertFalse(report["release_allowed"])


if __name__ == "__main__":
    unittest.main()
