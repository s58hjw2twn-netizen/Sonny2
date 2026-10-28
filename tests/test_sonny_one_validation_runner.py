import unittest
from unittest.mock import patch
from sonny_one.development_controller.validation_runner import (
    COMMANDS, execute_validation,
)


class ValidationRunnerTests(unittest.TestCase):
    def test_rejects_arbitrary_command(self):
        with self.assertRaises(ValueError):
            execute_validation("rm -rf .")

    def test_rejects_invalid_timeout(self):
        with self.assertRaises(ValueError):
            execute_validation("controller", 0)

    def test_immutable_command_list_uses_unittest(self):
        for command in COMMANDS.values():
            self.assertEqual(command[1:4], ["-m", "unittest", "discover"])
            self.assertNotIn("shell", command)

    def test_successful_subprocess_result(self):
        class Result:
            returncode = 0
            stdout = "OK"
            stderr = ""
        with patch("sonny_one.development_controller.validation_runner.subprocess.run", return_value=Result()) as run:
            result = execute_validation("controller")
        self.assertTrue(result["passed"])
        self.assertFalse(result["code_changes_made"])
        self.assertFalse(result["autonomous_coding"])
        self.assertFalse(run.call_args.kwargs["check"])

    def test_nonzero_return_is_failure(self):
        class Result:
            returncode = 2
            stdout = ""
            stderr = "failure"
        with patch("sonny_one.development_controller.validation_runner.subprocess.run", return_value=Result()):
            result = execute_validation("controller")
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
