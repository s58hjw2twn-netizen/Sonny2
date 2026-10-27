import unittest
from sonny_vision.quality.texture import texture_report

FACE=[[.2,.6,.2],[.6,.2,.6],[.2,.6,.2]]
class TextureTests(unittest.TestCase):
    def test_identical(self):
        self.assertTrue(texture_report(FACE,FACE)["texture_pass"])
    def test_oversmoothing(self):
        self.assertFalse(texture_report(FACE,[[.4]*3 for _ in range(3)])["texture_pass"])
    def test_flat_original(self):
        self.assertFalse(texture_report([[.4]*3 for _ in range(3)],FACE)["texture_pass"])
    def test_nonfinite(self):
        with self.assertRaises(ValueError): texture_report(FACE,[[float("nan")]*3 for _ in range(3)])
    def test_shape(self):
        with self.assertRaises(ValueError): texture_report(FACE,[[.2,.6]]*3)
    def test_tolerance(self):
        with self.assertRaises(ValueError): texture_report(FACE,FACE,max_relative_energy_change=float("nan"))
