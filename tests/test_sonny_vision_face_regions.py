import unittest
from unittest.mock import patch
from sonny_vision.quality.face_regions import crop_region, compare_manual_regions

GRID=[[0.,1.,0.,1.],[1.,0.,1.,0.],[0.,1.,0.,1.],[1.,0.,1.,0.]]

class FaceRegionTests(unittest.TestCase):
    def test_valid_crop(self):
        self.assertEqual(crop_region(GRID,(1,1,3,3)),[[0.,1.],[1.,0.]])
    def test_reject_bool_coordinates(self):
        with self.assertRaises(ValueError):
            crop_region(GRID,(True,0,3,3))
    def test_reject_out_of_bounds(self):
        with self.assertRaises(ValueError):
            crop_region(GRID,(0,0,5,4))
    def test_reject_tiny_crop(self):
        with self.assertRaises(ValueError):
            crop_region(GRID,(0,0,1,4))
    @patch("sonny_vision.quality.face_regions.load_grayscale",return_value=GRID)
    def test_pair_remains_review_only(self,_):
        result=compare_manual_regions("a.png","b.png",(0,0,4,4),(0,0,4,4))
        self.assertTrue(result["texture"]["texture_pass"])
        self.assertFalse(result["release_allowed"])
        self.assertFalse(result["identity_verified"])
    @patch("sonny_vision.quality.face_regions.load_grayscale",return_value=GRID)
    def test_mismatched_region_rejected(self,_):
        with self.assertRaises(ValueError):
            compare_manual_regions("a.png","b.png",(0,0,4,4),(0,0,3,3))
