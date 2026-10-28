"""Regression tests for precision edit contract."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from sonny_vision.constraint_contract import (
    ConstraintViolation, PrecisionRequest, authorize_image_method,
    verify_outside_mask, assert_completion,
)


class PrecisionContractTests(unittest.TestCase):
    def test_denies_whole_image_generator(self):
        with self.assertRaises(ConstraintViolation):
            authorize_image_method(
                PrecisionRequest(True, False), "full_image_generator")

    def test_denies_unverified_historical_reference(self):
        with self.assertRaises(ConstraintViolation):
            authorize_image_method(
                PrecisionRequest(True, True, "1991-order", False),
                "pixel_locked_composite")

    def test_allows_verified_precision_method(self):
        authorize_image_method(
            PrecisionRequest(True, True, "1991-order", True),
            "pixel_locked_composite")

    def test_rejects_outside_mask_change(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            src = Image.new("RGB", (4, 4), "white")
            dst = src.copy()
            dst.putpixel((0, 0), (0, 0, 0))
            mask = Image.new("L", (4, 4), 0)
            mask.putpixel((2, 2), 255)
            src.save(p / "src.png")
            dst.save(p / "dst.png")
            mask.save(p / "mask.png")
            with self.assertRaises(ConstraintViolation):
                verify_outside_mask(p / "src.png", p / "dst.png", p / "mask.png")

    def test_accepts_inside_mask_change(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)
            src = Image.new("RGB", (4, 4), "white")
            dst = src.copy()
            dst.putpixel((2, 2), (0, 0, 0))
            mask = Image.new("L", (4, 4), 0)
            mask.putpixel((2, 2), 255)
            src.save(p / "src.png")
            dst.save(p / "dst.png")
            mask.save(p / "mask.png")
            result = verify_outside_mask(p / "src.png", p / "dst.png", p / "mask.png")
            self.assertEqual(result["inside_changed_pixels"], 1)

    def test_denies_false_completion(self):
        with self.assertRaises(ConstraintViolation):
            assert_completion(pixel_verified=True, historical_claim=True,
                              period_reference_verified=False,
                              independent_review=True)


if __name__ == "__main__":
    unittest.main()
