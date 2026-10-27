import unittest
from unittest.mock import patch
from sonny_vision.quality.registration import translated_box, compare_translated_region

ORIGINAL=[[0.,1.,0.,0.],[1.,0.,0.,0.],[0.,0.,0.,0.],[0.,0.,0.,0.]]
RESTORED=[[0.,0.,1.,0.],[0.,1.,0.,0.],[0.,0.,0.,0.],[0.,0.,0.,0.]]

class RegistrationTests(unittest.TestCase):
    def test_translation(self):
        self.assertEqual(translated_box((0,0,2,2),1,0),(1,0,3,2))
    def test_boolean_shift_rejected(self):
        with self.assertRaises(ValueError):
            translated_box((0,0,2,2),True,0)
    def test_invalid_box_rejected(self):
        with self.assertRaises(ValueError):
            translated_box((0,0,True,2),1,0)
    @patch("sonny_vision.quality.registration.load_grayscale",side_effect=[ORIGINAL,RESTORED])
    def test_shifted_pair(self,_):
        result=compare_translated_region("a.png","b.png",(0,0,2,2),dx=1)
        self.assertTrue(result["texture"]["texture_pass"])
        self.assertFalse(result["alignment_verified"])
        self.assertFalse(result["release_allowed"])
    @patch("sonny_vision.quality.registration.load_grayscale",side_effect=[ORIGINAL,RESTORED])
    def test_out_of_bounds_shift(self,_):
        with self.assertRaises(ValueError):
            compare_translated_region("a.png","b.png",(0,0,2,2),dx=4)
