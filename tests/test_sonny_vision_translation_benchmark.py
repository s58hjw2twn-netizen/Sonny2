import unittest
from sonny_vision.quality.translation_benchmark import run_translation_benchmark

class TranslationBenchmarkTests(unittest.TestCase):
    def test_deterministic_benchmark(self):
        result=run_translation_benchmark()
        self.assertEqual(result["synthetic_cases"],6)
        self.assertEqual(result["correct"],6)
        self.assertTrue(result["flat_rejected"])
        self.assertFalse(result["real_photo_validation"])
        self.assertFalse(result["identity_verified"])
    def test_repeatable(self):
        self.assertEqual(run_translation_benchmark(),run_translation_benchmark())
