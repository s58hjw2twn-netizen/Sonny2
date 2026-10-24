import unittest
from sonny_one.causal_apl_bridge import apl_self_prediction_report


def record(cid, probability, eligible):
    code = 0 if eligible else 1
    report = {'candidate_id': cid,
              'status': 'ELIGIBLE_FOR_HUMAN_REVIEW' if eligible else 'REJECTED'}
    for key in ('baseline_deterministic', 'baseline_heldout',
                'deterministic', 'heldout'):
        report[key] = {'exit_code': code}
    return {'candidate_id': cid, 'predicted_pass': probability, 'report': report}


class AplBridgeTests(unittest.TestCase):
    def test_success(self):
        result = apl_self_prediction_report([record('a', .8, True)])
        self.assertAlmostEqual(result['self_model']['brier_score'], .04)
        self.assertFalse(result['provenance_verified'])
        self.assertFalse(result['improvement_proven'])

    def test_failure(self):
        result = apl_self_prediction_report([record('b', .8, False)])
        self.assertAlmostEqual(result['self_model']['brier_score'], .64)

    def test_mismatched_identity_rejected(self):
        item = record('a', .5, True)
        item['report']['candidate_id'] = 'b'
        with self.assertRaises(ValueError):
            apl_self_prediction_report([item])

    def test_incomplete_evaluation_rejected(self):
        item = record('a', .5, True)
        del item['report']['heldout']
        with self.assertRaises(ValueError):
            apl_self_prediction_report([item])

    def test_duplicate_candidate_rejected(self):
        with self.assertRaises(ValueError):
            apl_self_prediction_report([record('a', .5, True),
                                        record('a', .5, True)])

    def test_invalid_probability_rejected(self):
        with self.assertRaises(ValueError):
            apl_self_prediction_report([record('a', float('nan'), True)])


if __name__ == '__main__':
    unittest.main()
