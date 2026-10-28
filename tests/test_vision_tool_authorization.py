import tempfile
import unittest
from pathlib import Path
from sonny_vision.assurance import AssuranceError, FailureLedger
from sonny_vision.tool_authorization import (
    TaskPolicy, ToolCapability, authorize_tool, execute_authorized)


class ToolAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = FailureLedger(Path(self.tmp.name) / "failures.jsonl")
        self.policy = TaskPolicy("collar", ("masked_editor", "whole_image_generator"))
        self.masked = ToolCapability("masked_editor", True, True, True)
        self.generator = ToolCapability("whole_image_generator", False, False, False)

    def test_deny_whole_image_generator(self):
        result = authorize_tool(self.policy, self.generator, self.ledger, reference_id="usmc:1987")
        self.assertEqual(result["reason"], "cannot_enforce_preservation")

    def test_deny_missing_reference(self):
        self.assertEqual(authorize_tool(self.policy, self.masked, self.ledger)["reason"],
                         "missing_authoritative_reference")

    def test_authorize_qualified_tool(self):
        self.assertEqual(authorize_tool(self.policy, self.masked, self.ledger,
                                        reference_id="usmc:1987")["status"], "authorized")

    def test_no_side_effect_when_denied(self):
        calls = []
        with self.assertRaises(AssuranceError):
            execute_authorized(self.policy, self.generator, self.ledger,
                               lambda: calls.append("executed"), reference_id="usmc:1987")
        self.assertEqual(calls, [])

    def test_execute_when_authorized(self):
        self.assertEqual(execute_authorized(self.policy, self.masked, self.ledger,
                                            lambda: "ok", reference_id="usmc:1987"), "ok")

    def test_block_repeat_failure(self):
        for i in range(2):
            self.ledger.record(task_type="collar", method="masked_editor",
                               failure_code="failed_check", evidence_ref=str(i))
        self.assertEqual(authorize_tool(self.policy, self.masked, self.ledger,
                                        reference_id="usmc:1987")["reason"], "repeated_failure")

    def test_deny_unlisted_tool(self):
        unknown = ToolCapability("unknown", True, True, True)
        self.assertEqual(authorize_tool(self.policy, unknown, self.ledger,
                                        reference_id="usmc:1987")["reason"], "method_not_allowlisted")


if __name__ == "__main__":
    unittest.main()
