import tempfile
import unittest
from pathlib import Path
from sonny_vision.restoration.photo_face_lock import compose_face_locked_png

class PhotoFaceLockTests(unittest.TestCase):
    def setUp(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("optional Pillow not installed")
        self.Image=Image
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a=Path(self.temp.name)/"a.png"
        self.b=Path(self.temp.name)/"b.png"
        self.out=Path(self.temp.name)/"out.png"
        Image.new("RGB",(20,20),(10,20,30)).save(self.a)
        Image.new("RGB",(20,20),(200,210,220)).save(self.b)
    def test_two_faces_preserved(self):
        result=compose_face_locked_png(self.a,self.b,self.out,
            [(0.1,0.1,0.3,0.3),(0.6,0.6,0.8,0.8)],expected_faces=2)
        with self.Image.open(self.out) as image:
            self.assertEqual(image.getpixel((4,4)),(10,20,30))
            self.assertEqual(image.getpixel((14,14)),(10,20,30))
            self.assertEqual(image.getpixel((19,0)),(200,210,220))
        self.assertTrue(result["protected_pixels_identical"])
        self.assertFalse(result["release_allowed"])
    def test_missing_face_fails(self):
        with self.assertRaises(ValueError):
            compose_face_locked_png(self.a,self.b,self.out,[(.1,.1,.3,.3)],expected_faces=2)
    def test_prevent_input_overwrite(self):
        with self.assertRaises(ValueError):
            compose_face_locked_png(self.a,self.b,self.a,[(.1,.1,.3,.3)],expected_faces=1)
    def test_dimension_mismatch(self):
        self.Image.new("RGB",(21,20),(0,0,0)).save(self.b)
        with self.assertRaises(ValueError):
            compose_face_locked_png(self.a,self.b,self.out,[(.1,.1,.3,.3)],expected_faces=1)
