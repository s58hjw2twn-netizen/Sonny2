import unittest
from sonny_vision.quality.review_pipeline import evaluate_restoration

FACE = {'left_eye': (.3, .3), 'right_eye': (.7, .3), 'nose': (.5, .5), 'mouth_left': (.4, .7), 'mouth_right': (.6, .7), 'chin': (.5, .9)}
CROP = [[.2, .6, .2], [.6, .2, .6], [.2, .6, .2]]

def specimen(restored=None, landmarks=None):
    return {'landmark_stages': landmarks or [FACE, FACE], 'original_crop': CROP,
            'restored_crop': restored if restored is not None else CROP}

class PipelineTests(unittest.TestCase):
    def test_missing_identity_blocks(self):
        self.assertFalse(evaluate_restoration([specimen()])['release_allowed'])
    def test_owner_approval_blocks(self):
        self.assertFalse(evaluate_restoration([specimen()], identity_scores=[.99], reference_review_passed=True)['release_allowed'])
    def test_all_provisional_inputs(self):
        self.assertTrue(evaluate_restoration([specimen()], identity_scores=[.99], reference_review_passed=True, owner_approved=True)['release_allowed'])
    def test_one_bad_face_blocks(self):
        self.assertFalse(evaluate_restoration([specimen(), specimen(restored=[[.4]*3]*3)], identity_scores=[.99, .99], reference_review_passed=True, owner_approved=True)['release_allowed'])
    def test_drift_blocks(self):
        changed = dict(FACE, nose=(.55, .5))
        self.assertFalse(evaluate_restoration([specimen(landmarks=[FACE, changed])], identity_scores=[.99], reference_review_passed=True, owner_approved=True)['release_allowed'])
    def test_missing_evidence_blocks(self):
        self.assertFalse(evaluate_restoration([{}], identity_scores=[.99], reference_review_passed=True, owner_approved=True)['release_allowed'])
    def test_empty_faces_blocks(self):
        self.assertFalse(evaluate_restoration([], owner_approved=True, reference_review_passed=True)['release_allowed'])
