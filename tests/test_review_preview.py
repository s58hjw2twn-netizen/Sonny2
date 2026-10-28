import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops
from sonny_vision.review_preview import make_review_preview

class ReviewPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        Image.new("RGB", (800, 600), (20, 30, 40)).save(self.source)

    def test_preview_watermark_and_audit(self):
        preview, audit = self.root / "preview.png", self.root / "audit.json"
        result = make_review_preview(self.source, preview, audit, case_id="case-001")
        self.assertEqual(result["status"], "watermarked_review_only")
        self.assertFalse(result["customer_approved"])
        self.assertIsNotNone(ImageChops.difference(Image.open(self.source), Image.open(preview)).getbbox())
        self.assertTrue(audit.exists())

    def test_source_is_unchanged(self):
        before = self.source.read_bytes()
        make_review_preview(self.source, self.root / "preview.png",
                            self.root / "audit.json", case_id="case-002")
        self.assertEqual(before, self.source.read_bytes())

    def test_cannot_overwrite_source(self):
        with self.assertRaises(ValueError):
            make_review_preview(self.source, self.source, self.root / "audit.json", case_id="case-003")

    def test_case_id_required(self):
        with self.assertRaises(ValueError):
            make_review_preview(self.source, self.root / "preview.png",
                                self.root / "audit.json", case_id="")
if __name__ == "__main__":
    unittest.main()
