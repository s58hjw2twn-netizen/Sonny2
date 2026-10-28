import unittest

from sonny_vision.restoration.face_protection import protected_boxes, is_protected


class FaceProtectionTests(unittest.TestCase):
    def test_two_faces_protected(self):
        boxes = protected_boxes([(0.1, 0.2, 0.3, 0.5), (0.6, 0.2, 0.8, 0.5)])
        self.assertEqual(len(boxes), 2)
        self.assertTrue(is_protected(0.2, 0.3, boxes))
        self.assertTrue(is_protected(0.7, 0.3, boxes))
        self.assertFalse(is_protected(0.45, 0.9, boxes))

    def test_padding_clamps_at_image_edges(self):
        box = protected_boxes([(0.0, 0.0, 0.2, 0.2)], padding=1)[0]
        self.assertEqual(box[:2], (0.0, 0.0))

    def test_no_faces_fails_closed(self):
        with self.assertRaises(ValueError):
            protected_boxes([])

    def test_invalid_box_rejected(self):
        for box in [(0.4, 0.2, 0.1, 0.5), (0, 0, 2, 1), (0, 0, float("nan"), 1)]:
            with self.subTest(box=box), self.assertRaises(ValueError):
                protected_boxes([box])

    def test_invalid_padding_rejected(self):
        with self.assertRaises(ValueError):
            protected_boxes([(0.1, 0.1, 0.2, 0.2)], padding=float("nan"))


if __name__ == "__main__":
    unittest.main()
