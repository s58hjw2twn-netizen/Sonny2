import tempfile
import unittest
from pathlib import Path
from sonny_vision.quality.pgm_fixture import read_pgm
from sonny_vision.quality.texture import texture_report

class PgmFixtureTests(unittest.TestCase):
    def write(self, data):
        folder = tempfile.TemporaryDirectory()
        path = Path(folder.name) / "crop.pgm"
        path.write_bytes(data)
        self.addCleanup(folder.cleanup)
        return path

    def test_read_and_compare_real_bytes(self):
        path = self.write(b"P5\n2 2\n255\n" + bytes([0,255,255,0]))
        pixels = read_pgm(path)
        self.assertEqual(pixels, [[0.,1.],[1.,0.]])
        self.assertTrue(texture_report(pixels,pixels)["texture_pass"])

    def test_reject_truncated(self):
        with self.assertRaises(ValueError):
            read_pgm(self.write(b"P5\n2 2\n255\n" + bytes([1])))

    def test_reject_invalid_magic(self):
        with self.assertRaises(ValueError):
            read_pgm(self.write(b"P2\n2 2\n255\n" + bytes([1,2,3,4])))

    def test_reject_oversized(self):
        with self.assertRaises(ValueError):
            read_pgm(self.write(b"P5\n10000 10000\n255\n"))

if __name__ == "__main__":
    unittest.main()
