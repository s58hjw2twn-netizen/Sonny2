import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from sonny_vision.precision_release_gate import (
    ReleaseDenied, verify_precision_edit, authorize_release)

class TestPrecisionReleaseGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = Path(self.tmp.name)
        self.source, self.candidate, self.mask = [p / n for n in ("src.png","dst.png","mask.png")]
        a = np.zeros((100,100,3),dtype=np.uint8)
        Image.fromarray(a).save(self.source)
        a[45,45] = [200,150,10]
        Image.fromarray(a).save(self.candidate)
        m = np.zeros((100,100),dtype=np.uint8)
        m[40:50,40:50] = 255
        Image.fromarray(m).save(self.mask)
        self.options = dict(method="pixel_locked_composite",reference_id="period-reference",
                            reference_verified=True,mask_approved=True,
                            independent_review="reviewer:pass")

    def check(self, **changes):
        return verify_precision_edit(self.source,self.candidate,self.mask,
                                     **(self.options | changes))

    def test_requires_customer_approval(self):
        with self.assertRaises(ReleaseDenied):
            authorize_release(self.check())

    def test_approved(self):
        self.assertTrue(authorize_release(self.check(customer_approved=True)))

    def test_rejects_full_generation(self):
        with self.assertRaises(ReleaseDenied):
            self.check(method="full_image_generation")

    def test_rejects_unverified_reference(self):
        with self.assertRaises(ReleaseDenied):
            self.check(reference_verified=False)

    def test_rejects_unapproved_mask(self):
        with self.assertRaises(ReleaseDenied):
            self.check(mask_approved=False)

    def test_rejects_missing_review(self):
        with self.assertRaises(ReleaseDenied):
            self.check(independent_review=None)

    def test_rejects_outside_changes(self):
        a = np.asarray(Image.open(self.candidate)).copy()
        a[0,0] = [255,255,255]
        Image.fromarray(a).save(self.candidate)
        with self.assertRaises(ReleaseDenied):
            self.check()

    def test_rejects_large_mask(self):
        Image.fromarray(np.full((100,100),255,dtype=np.uint8)).save(self.mask)
        with self.assertRaises(ReleaseDenied):
            self.check()

if __name__ == "__main__":
    unittest.main()
