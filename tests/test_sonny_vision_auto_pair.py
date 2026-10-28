import unittest
from unittest.mock import patch
from sonny_vision.quality.auto_pair import compare_auto_aligned_regions

def grids():
    a=[[0.]*7 for _ in range(7)]
    b=[[0.]*7 for _ in range(7)]
    pattern=[[.1,.8,.2],[.7,.3,.9],[.4,.6,.15]]
    for y in range(3):
        for x in range(3):
            a[y+2][x+2]=pattern[y][x]
            b[y+2][x+3]=pattern[y][x]
    return a,b

class AutoPairTests(unittest.TestCase):
    @patch("sonny_vision.quality.auto_pair.load_grayscale")
    def test_shifted_pair(self,load):
        load.side_effect=grids()
        result=compare_auto_aligned_regions("a.png","b.png",(2,2,5,5),max_shift=1)
        self.assertTrue(result["registration"]["accepted"])
        self.assertTrue(result["texture"]["texture_pass"])
        self.assertFalse(result["release_allowed"])
    @patch("sonny_vision.quality.auto_pair.load_grayscale")
    def test_low_texture_fails_closed(self,load):
        load.side_effect=[[[.5]*5 for _ in range(5)] for _ in range(2)]
        result=compare_auto_aligned_regions("a.png","b.png",(1,1,4,4))
        self.assertFalse(result["registration"]["accepted"])
        self.assertIsNone(result["texture"])
        self.assertFalse(result["identity_verified"])
    @patch("sonny_vision.quality.auto_pair.load_grayscale")
    def test_invalid_box_rejected(self,load):
        load.side_effect=grids()
        with self.assertRaises(ValueError):
            compare_auto_aligned_regions("a.png","b.png",(0,0,100,100))
