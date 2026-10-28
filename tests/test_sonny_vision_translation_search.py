import unittest
from sonny_vision.quality.translation_search import estimate_translation

class TranslationSearchTests(unittest.TestCase):
    def test_unique_shift(self):
        a=[[0.]*7 for _ in range(7)]
        b=[[0.]*7 for _ in range(7)]
        pattern=[[.1,.8,.2],[.7,.3,.9],[.4,.6,.15]]
        for y in range(3):
            for x in range(3):
                a[y+2][x+2]=pattern[y][x]
                b[y+2][x+3]=pattern[y][x]
        result=estimate_translation(a,b,(2,2,5,5),max_shift=1)
        self.assertTrue(result["accepted"])
        self.assertEqual((result["dx"],result["dy"]),(1,0))
        self.assertFalse(result["identity_verified"])
    def test_flat_rejected(self):
        grid=[[.5]*5 for _ in range(5)]
        self.assertEqual(estimate_translation(grid,grid,(1,1,4,4))["reason"],"low_texture")
    def test_repeated_pattern_ambiguous(self):
        a=[[0.,1.,0.,1.,0.,1.] for _ in range(4)]
        r=estimate_translation(a,a,(1,1,3,3),max_shift=2)
        self.assertFalse(r["accepted"])
    def test_invalid_radius(self):
        with self.assertRaises(ValueError):
            estimate_translation([[0.]*3]*3,[[0.]*3]*3,(0,0,2,2),max_shift=True)
    def test_invalid_pixels(self):
        a=[[.1,.8],[.7,float("nan")]]
        with self.assertRaises(ValueError):
            estimate_translation(a,a,(0,0,2,2))
