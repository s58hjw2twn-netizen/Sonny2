import tempfile
import unittest
from pathlib import Path

from PIL import Image
from sonny_vision.protected_edits import ProtectedEditError, validate_local_edit


class ProtectedEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.original = Path(self.tmp.name) / "original.png"
        self.candidate = Path(self.tmp.name) / "candidate.png"
        Image.new("RGB", (12, 12), "black").save(self.original)

    def make_candidate(self, position):
        image = Image.open(self.original)
        image.putpixel(position, (255, 0, 0))
        image.save(self.candidate)

    def test_allowed_edit(self):
        self.make_candidate((2, 2))
        result = validate_local_edit(self.original, self.candidate, [(1, 1, 4, 4)])
        self.assertEqual(result["changed_pixels"], 1)

    def test_reject_protected_pixel(self):
        self.make_candidate((8, 8))
        with self.assertRaises(ProtectedEditError):
            validate_local_edit(self.original, self.candidate, [(1, 1, 4, 4)])

    def test_reject_missing_regions(self):
        self.make_candidate((2, 2))
        with self.assertRaises(ProtectedEditError):
            validate_local_edit(self.original, self.candidate, [])

    def test_reject_dimension_change(self):
        Image.new("RGB", (13, 12), "black").save(self.candidate)
        with self.assertRaises(ProtectedEditError):
            validate_local_edit(self.original, self.candidate, [(1, 1, 4, 4)])


if __name__ == "__main__":
    unittest.main()
