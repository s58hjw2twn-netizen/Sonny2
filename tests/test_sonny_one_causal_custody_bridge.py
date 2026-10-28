import unittest
from sonny_one.apl.custody import seal_evidence
from sonny_one.causal_custody_bridge import custody_checked_apl_report


def sample():
    report = {"candidate_id": "c1", "status": "ELIGIBLE_FOR_HUMAN_REVIEW"}
    for k in ("baseline_deterministic", "baseline_heldout", "deterministic", "heldout"):
        report[k] = {"exit_code": 0}
    return [{"candidate_id": "c1", "predicted_pass": .8, "report": report}]


class CustodyBridgeTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 32
        self.records = sample()
        self.envelope = seal_evidence({"records": self.records}, self.key,
                                      custodian_id="independent-1")

    def check(self, records=None, envelope=None, key=None, cid="independent-1"):
        return custody_checked_apl_report(
            self.records if records is None else records,
            self.envelope if envelope is None else envelope,
            custodian_key=self.key if key is None else key,
            custodian_id=cid)

    def test_valid_custody(self):
        r = self.check()
        self.assertTrue(r["custody_mac_verified"])
        self.assertFalse(r["independent_grading_verified"])
        self.assertFalse(r["provenance_verified"])

    def test_wrong_key(self):
        with self.assertRaises(PermissionError):
            self.check(key=b"x" * 32)

    def test_wrong_custodian(self):
        with self.assertRaises(PermissionError):
            self.check(cid="unknown")

    def test_modified_probability(self):
        records = sample()
        records[0]["predicted_pass"] = .1
        with self.assertRaises(PermissionError):
            self.check(records=records)

    def test_modified_outcome(self):
        records = sample()
        records[0]["report"]["status"] = "REJECTED"
        with self.assertRaises(PermissionError):
            self.check(records=records)

    def test_empty_records(self):
        with self.assertRaises(ValueError):
            self.check(records=[])


if __name__ == "__main__":
    unittest.main()
