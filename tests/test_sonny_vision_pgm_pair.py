import tempfile
import unittest
from pathlib import Path
from sonny_vision.quality.pgm_pair import evaluate_pgm_pair

def pgm(pixels):
    return b"P5\n3 3\n255\n" + bytes(pixels)

class PairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.a = Path(self.temp.name) / "original.pgm"
        self.b = Path(self.temp.name) / "restored.pgm"
        self.a.write_bytes(pgm([0,255,0,255,0,255,0,255,0]))
        self.b.write_bytes(self.a.read_bytes())

    def test_matching_pair(self):
        result = evaluate_pgm_pair(self.a,self.b)
        self.assertTrue(result["texture"]["texture_pass"])
        self.assertEqual(result["original_sha256"],result["restored_sha256"])
        self.assertFalse(result["release_allowed"])
        self.assertFalse(result["identity_verified"])

    def test_smoothing_detected(self):
        self.b.write_bytes(pgm([128]*9))
        result = evaluate_pgm_pair(self.a,self.b)
        self.assertFalse(result["texture"]["texture_pass"])
        self.assertNotEqual(result["original_sha256"],result["restored_sha256"])

    def test_invalid_file_rejected(self):
        self.b.write_bytes(b"bad")
        with self.assertRaises(ValueError):
            evaluate_pgm_pair(self.a,self.b)

    def test_dimension_mismatch_rejected(self):
        self.b.write_bytes(b"P5\n2 2\n255\n"+bytes([0,1,2,3]))
        with self.assertRaises(ValueError):
            evaluate_pgm_pair(self.a,self.b)

if __name__=="__main__":
    unittest.main()
