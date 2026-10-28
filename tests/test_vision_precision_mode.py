import tempfile
import unittest
from pathlib import Path
from PIL import Image
from sonny_vision.precision_mode import EditRequest, apply_precision_edit
from sonny_vision.protected_edits import ProtectedEditError


class PrecisionModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.source, self.patch = root / "source.png", root / "patch.png"
        self.mask, self.output = root / "mask.png", root / "out.png"
        Image.new("RGB", (8, 8), "black").save(self.source)
        patch = Image.new("RGB", (8, 8), "black")
        patch.putpixel((2, 2), (255, 0, 0))
        patch.save(self.patch)
        mask = Image.new("L", (8, 8), 0)
        mask.putpixel((2, 2), 255)
        mask.save(self.mask)

    def request(self, regions=((1, 1, 4, 4),)):
        return EditRequest(str(self.source), str(self.patch), str(self.mask),
                           str(self.output), regions, "1987 reference pending review")

    def test_masked_edit_and_original_unchanged(self):
        audit = apply_precision_edit(self.request())
        self.assertEqual(audit["changed_pixels"], 1)
        self.assertFalse(audit["customer_approved"])
        self.assertFalse(audit["historical_accuracy_verified"])
        with Image.open(self.source) as before, Image.open(self.output) as after:
            self.assertEqual(before.getpixel((2, 2)), (0, 0, 0))
            self.assertEqual(after.getpixel((2, 2)), (255, 0, 0))
            self.assertEqual(after.getpixel((5, 5)), (0, 0, 0, 255))

    def test_reject_mask_outside_region(self):
        with self.assertRaises(ProtectedEditError):
            apply_precision_edit(self.request(((4, 4, 7, 7),)))
        self.assertFalse(self.output.exists())

    def test_reject_overwriting_source(self):
        req = self.request()
        req = EditRequest(req.source, req.reference_patch, req.mask,
                          req.source, req.allowed_regions, req.reference_note)
        with self.assertRaises(ProtectedEditError):
            apply_precision_edit(req)

    def test_reject_existing_output(self):
        self.output.write_bytes(b"existing")
        with self.assertRaises(ProtectedEditError):
            apply_precision_edit(self.request())

    def test_reject_soft_mask(self):
        mask = Image.new("L", (8, 8), 0)
        mask.putpixel((2, 2), 128)
        mask.save(self.mask)
        with self.assertRaises(ProtectedEditError):
            apply_precision_edit(self.request())

    def test_reject_empty_mask(self):
        Image.new("L", (8, 8), 0).save(self.mask)
        with self.assertRaises(ProtectedEditError):
            apply_precision_edit(self.request())


if __name__ == "__main__":
    unittest.main()
