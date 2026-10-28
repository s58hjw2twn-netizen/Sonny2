import unittest
from sonny_one.development_controller.execution_receipt import validate_execution_receipt

PARENT = "a" * 40
COMMIT = "b" * 40


def receipt():
    return {"task_id": "DEV-001", "parent_sha": PARENT, "commit_sha": COMMIT,
            "branch": "research/apl-001", "test_run_id": "1001",
            "test_conclusion": "success", "policy_run_id": "1002",
            "policy_conclusion": "success", "independent_verification": True}


class ExecutionReceiptTests(unittest.TestCase):
    def check(self, value):
        return validate_execution_receipt(value, expected_task_id="DEV-001",
                                          expected_parent_sha=PARENT)

    def test_valid_shape(self):
        self.assertTrue(self.check(receipt())["accepted_shape"])
        self.assertFalse(self.check(receipt())["independently_verified_by_this_module"])

    def test_wrong_task(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "task_id": "APP-002"})

    def test_wrong_parent(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "parent_sha": "c" * 40})

    def test_no_new_commit(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "commit_sha": PARENT})

    def test_wrong_branch(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "branch": "main"})

    def test_failed_ci(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "test_conclusion": "failure"})

    def test_no_independent_verification(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "independent_verification": False})

    def test_same_ci_run_not_accepted(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "policy_run_id": "1001"})

    def test_unexpected_field(self):
        with self.assertRaises(ValueError):
            self.check({**receipt(), "force": True})


if __name__ == "__main__":
    unittest.main()
