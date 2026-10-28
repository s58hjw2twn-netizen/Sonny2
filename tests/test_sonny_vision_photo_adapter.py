import tempfile
import unittest
from pathlib import Path
from sonny_vision.quality.photo_adapter import load_grayscale, compare_image_pair

class PhotoAdapterTests(unittest.TestCase):
    def test_unsupported_extension(self):
        with self.assertRaises(ValueError):
            load_grayscale("photo.gif")
    def test_invalid_pixel_limit(self):
        with self.assertRaises(ValueError):
            load_grayscale("photo.png",max_pixels=True)
    def test_missing_image_fails(self):
        with self.assertRaises((RuntimeError,ValueError)):
            load_grayscale("nonexistent-photo.png")
    def test_real_png_when_pillow_available(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("optional Pillow not installed")
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/"a.png"
            b=Path(d)/"b.png"
            image=Image.new("L",(3,3))
            image.putdata([0,255,0,255,0,255,0,255,0])
            image.save(a)
            image.save(b)
            result=compare_image_pair(a,b)
            self.assertTrue(result["texture"]["texture_pass"])
            self.assertFalse(result["release_allowed"])
            self.assertFalse(result["identity_verified"])
