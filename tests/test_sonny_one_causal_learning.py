import unittest
from sonny_one.causal_learning import calibration_report

class FakeModel:
    def __init__(self, pairs):
        self.pairs = pairs
    def report(self):
        return {'unobserved': 2, 'outcomes': [
            {'prediction': {'capability': cap, 'probability': prob},
             'observation': {'succeeded': success}}
            for cap, prob, success in self.pairs]}

class Tests(unittest.TestCase):
    def test_no_data(self):
        self.assertEqual(calibration_report(FakeModel([]))['capabilities'], {})
    def test_small_sample_abstains(self):
        x = calibration_report(FakeModel([('memory', .9, False)]))
        self.assertEqual(x['capabilities']['memory']['recommendation'], 'insufficient_evidence')
    def test_overconfidence(self):
        x = calibration_report(FakeModel([('memory', .9, False)]*5))
        self.assertEqual(x['capabilities']['memory']['recommendation'], 'review_overconfidence')
    def test_underconfidence(self):
        x = calibration_report(FakeModel([('memory', .1, True)]*5))
        self.assertEqual(x['capabilities']['memory']['recommendation'], 'review_underconfidence')
    def test_calibrated(self):
        x = calibration_report(FakeModel([('memory', .5, True),('memory', .5, False)]*3))
        self.assertEqual(x['capabilities']['memory']['recommendation'], 'monitor')
    def test_separate_capabilities(self):
        x = calibration_report(FakeModel([('a', .9, False)]*5+[('b', .1, True)]*5))
        self.assertEqual(len(x['capabilities']), 2)
    def test_invalid_sample(self):
        for x in (0, 1, True, 2.5):
            with self.subTest(x=x), self.assertRaises(ValueError):
                calibration_report(FakeModel([]), min_samples=x)

if __name__ == '__main__':
    unittest.main()
