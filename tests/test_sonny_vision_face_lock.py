import unittest
from sonny_vision.restoration.face_lock import face_lock_composite

class FaceLockTests(unittest.TestCase):
    def setUp(self):
        self.original=[[(10,20,30)]*10 for _ in range(10)]
        self.enhanced=[[(200,210,220)]*10 for _ in range(10)]
    def test_two_faces_locked_and_background_changed(self):
        r=face_lock_composite(self.original,self.enhanced,
            [(0.1,0.1,0.3,0.3),(0.6,0.6,0.8,0.8)],expected_faces=2)
        self.assertTrue(r["protected_pixels_identical"])
        self.assertEqual(r["pixels"][2][2],(10,20,30))
        self.assertEqual(r["pixels"][7][7],(10,20,30))
        self.assertEqual(r["pixels"][0][9],(200,210,220))
        self.assertFalse(r["release_allowed"])
    def test_missing_face_rejected(self):
        with self.assertRaises(ValueError):
            face_lock_composite(self.original,self.enhanced,[(.1,.1,.3,.3)],expected_faces=2)
    def test_empty_faces_rejected(self):
        with self.assertRaises(ValueError):
            face_lock_composite(self.original,self.enhanced,[],expected_faces=1)
    def test_invalid_pixel_rejected(self):
        self.enhanced[0][0]=(True,0,0)
        with self.assertRaises(ValueError):
            face_lock_composite(self.original,self.enhanced,[(.1,.1,.3,.3)],expected_faces=1)
    def test_dimension_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            face_lock_composite(self.original,self.enhanced[:-1],[(.1,.1,.3,.3)],expected_faces=1)
