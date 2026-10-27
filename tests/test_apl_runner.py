"""Runner orchestration tests with fake git/docker; no Docker or network required."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from sonny_one.apl import runner


class TestRunnerGuardrails(unittest.TestCase):
    def test_rejects_unpinned_image_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for name in ("source", "trusted", "heldout"):
                (p / name).mkdir()
            (p / "candidate.diff").write_text("not relevant")
            with patch.object(runner, "execute") as execute:
                with self.assertRaises(ValueError):
                    runner.evaluate(p / "source", "a" * 40, p / "candidate.diff",
                                    p / "trusted", p / "heldout", "python:latest",
                                    p / "ledger")
                execute.assert_not_called()

    def test_rejects_test_suite_inside_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "source" / "tests").mkdir(parents=True)
            (p / "heldout").mkdir()
            (p / "candidate.diff").write_text("not relevant")
            with self.assertRaises(ValueError):
                runner.evaluate(p / "source", "a" * 40, p / "candidate.diff",
                                p / "source" / "tests", p / "heldout",
                                "runner@sha256:" + "a" * 64, p / "ledger")


    def test_suite_fingerprint_changes_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "test_sample.py").write_text("assert True")
            before = runner.suite_fingerprint(p)
            (p / "test_sample.py").write_text("assert False")
            self.assertNotEqual(before, runner.suite_fingerprint(p))

    def test_suite_fingerprint_stable_across_creation_order(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for name in ("b.py", "a.py"):
                (Path(a) / name).write_text(name)
            for name in ("a.py", "b.py"):
                (Path(b) / name).write_text(name)
            self.assertEqual(runner.suite_fingerprint(Path(a)),
                             runner.suite_fingerprint(Path(b)))

    def test_suite_fingerprint_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / "test.py").write_text("pass")
            (p / "alias.py").symlink_to(p / "test.py")
            with self.assertRaises(ValueError):
                runner.suite_fingerprint(p)


    def test_docker_invocation_has_network_and_privilege_restrictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            workspace, suite = p / "workspace", p / "suite"
            workspace.mkdir()
            suite.mkdir()
            fake = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            with patch.object(runner, "execute", return_value=fake) as execute:
                result = runner.docker_test("runner@sha256:" + "a" * 64,
                                            workspace, suite, 30)
            argv = execute.call_args.args[0]
            self.assertEqual(result["exit_code"], 0)
            for restriction in ("--network=none", "--cap-drop=ALL",
                                "--security-opt=no-new-privileges",
                                "--read-only", "--pull=never",
                                "--user=65534:65534"):
                self.assertIn(restriction, argv)
            self.assertIn("--volume=" + str(workspace) + ":/src:ro", argv)
            self.assertIn("--volume=" + str(suite) + ":/trusted:ro", argv)
            self.assertIn("--env=SONNY_APL_EVALUATION=1", argv)
            self.assertIn("--env=SONNY_APL_CANDIDATE_TEST=0", argv)

    def test_candidate_mode_is_explicit(self):
        with patch.object(runner, "execute") as execute:
            execute.return_value = type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()
            runner.docker_test("runner@sha256:" + "a" * 64,
                               Path("/tmp/workspace"), Path("/tmp/suite"), 30,
                               candidate=True)
        self.assertIn("--env=SONNY_APL_CANDIDATE_TEST=1", execute.call_args.args[0])

    def test_evaluate_fails_before_candidate_execution_if_image_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            for name in ("source", "trusted", "heldout"):
                (p / name).mkdir()
            (p / "candidate.diff").write_text("not relevant")
            with patch.object(runner, "preflight_docker_image",
                              side_effect=RuntimeError("image unavailable")) as preflight:
                with patch.object(runner, "docker_test") as docker:
                    with self.assertRaisesRegex(RuntimeError, "image unavailable"):
                        runner.evaluate(p / "source", "a" * 40, p / "candidate.diff",
                                        p / "trusted", p / "heldout",
                                        "runner@sha256:" + "a" * 64, p / "ledger")
                    preflight.assert_called_once()
                    docker.assert_not_called()

    def test_preflight_rejects_unpinned_image_without_docker(self):
        with patch.object(runner, "execute") as execute:
            with self.assertRaises(ValueError):
                runner.preflight_docker_image("python:latest")
            execute.assert_not_called()

    def test_preflight_accepts_only_matching_local_digest(self):
        image = "runner@sha256:" + "a" * 64
        fake = type("Result", (), {"returncode": 0,
            "stdout": __import__("json").dumps([image]), "stderr": ""})()
        with patch.object(runner, "execute", return_value=fake) as execute:
            result = runner.preflight_docker_image(image)
        self.assertTrue(result["locally_verified"])
        self.assertFalse(result["container_executed"])
        self.assertEqual(execute.call_args.args[0][:3],
                         ["docker", "image", "inspect"])

    def test_preflight_rejects_mismatched_or_missing_digest(self):
        image = "runner@sha256:" + "a" * 64
        for code, output in ((0, '["other@sha256:' + 'b' * 64 + '"]'),
                             (0, "not-json"), (1, "")):
            fake = type("Result", (), {"returncode": code,
                "stdout": output, "stderr": ""})()
            with patch.object(runner, "execute", return_value=fake):
                with self.assertRaises(RuntimeError):
                    runner.preflight_docker_image(image)

    def test_docker_timeout_is_rejected(self):
        import subprocess
        with patch.object(runner, "execute",
                          side_effect=subprocess.TimeoutExpired(["docker"], 1)):
            result = runner.docker_test("runner@sha256:" + "a" * 64,
                                        Path("/tmp/workspace"), Path("/tmp/suite"), 1)
        self.assertEqual(result["exit_code"], -1)
        self.assertEqual(result["error"], "TimeoutExpired")


if __name__ == "__main__":
    unittest.main()
