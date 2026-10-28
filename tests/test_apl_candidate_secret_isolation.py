"""Regression checks for APL Docker candidate isolation (no Docker needed)."""
import unittest
from unittest.mock import patch
from sonny_one.apl.runner import docker_test


class CandidateIsolationTests(unittest.TestCase):
    @patch("sonny_one.apl.runner.execute")
    def test_candidate_receives_no_provider_or_git_credentials(self, execute):
        execute.return_value.returncode = 0
        execute.return_value.stdout = ""
        execute.return_value.stderr = ""
        with patch("sonny_one.apl.runner.uuid.uuid4") as unique:
            unique.return_value.hex = "a" * 32
            docker_test("python@sha256:" + "b" * 64, "/tmp/work", "/tmp/suite",
                        30, candidate=True, framework="unittest")
        args = execute.call_args.args[0]
        self.assertEqual(args[0:2], ["docker", "run"])
        self.assertIn("--network=none", args)
        self.assertIn("--cap-drop=ALL", args)
        self.assertIn("--security-opt=no-new-privileges", args)
        self.assertIn("--read-only", args)
        self.assertIn("--user=65534:65534", args)
        self.assertIn("--volume=/tmp/work:/src:ro", args)
        self.assertIn("--volume=/tmp/suite:/trusted:ro", args)
        self.assertIn("--env=SONNY_APL_CANDIDATE_TEST=1", args)
        self.assertFalse(any("GEMINI_API_KEY" in arg or "GITHUB_TOKEN" in arg or
                             "GH_TOKEN" in arg or "ACTIONS_RUNTIME_TOKEN" in arg
                             for arg in args))
        self.assertFalse(any(arg.startswith("--env-file") or
                             arg.startswith("--volume=/home/") or
                             arg.startswith("--volume=/var/run/docker.sock")
                             for arg in args))


if __name__ == "__main__":
    unittest.main()
