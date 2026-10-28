import unittest
from sonny_vision.quality.photometric_benchmark import photometric_stress_benchmark

class PhotometricBenchmarkTests(unittest.TestCase):
    def test_cases_are_recorded(self):
        r=photometric_stress_benchmark()
        self.assertEqual(r["total"],4)
        self.assertEqual(len(r["cases"]),4)
        self.assertFalse(r["real_photo_validation"])
    def test_baseline_correct(self):
        r=photometric_stress_benchmark()
        self.assertTrue(r["cases"][0]["correct"])
    def test_repeatability(self):
        self.assertEqual(photometric_stress_benchmark(),photometric_stress_benchmark())
