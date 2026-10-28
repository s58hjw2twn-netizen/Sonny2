"""Manual-only Gemini generation and Docker-isolated functional trial.

Requires an explicitly configured GEMINI_API_KEY. No commits or deployments.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile

from sonny.coding_model_provider import generate_and_stage_patch
from sonny.research_agent import Task
from run_isolated_coding_trial import run_container


def main():
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY is required for a live trial")
    source = "def add(a, b):\n    return a - b\n"
    task = Task("LIVE1", "Correct add(a,b) so it returns the sum of a and b. Preserve the function name and signature.", ("sonny/example.py",), "low")
    staged = generate_and_stage_patch(task, {"sonny/example.py": source})
    candidate = staged["candidate"]["sonny/example.py"]
    assert staged["provider"] == "gemini"
    assert staged["commit_allowed"] is False
    assert staged["independently_verified"] is False
    tests = (
        "import unittest\n"
        "from sonny.example import add\n"
        "class ExampleTest(unittest.TestCase):\n"
        "    def test_positive(self): self.assertEqual(add(2, 3), 5)\n"
        "    def test_negative(self): self.assertEqual(add(-2, -3), -5)\n"
        "    def test_zero(self): self.assertEqual(add(0, 4), 4)\n"
    )
    results = {}
    with tempfile.TemporaryDirectory(prefix="sonny-live-") as root:
        for name, code in (("baseline", source), ("candidate", candidate)):
            workspace = Path(root) / name
            (workspace / "sonny").mkdir(parents=True)
            (workspace / "sonny" / "__init__.py").write_text("")
            source_path = workspace / "sonny" / "example.py"
            source_path.write_text(code)
            (workspace / "test_example.py").write_text(tests)
            for file in workspace.rglob("*"):
                if file.is_file():
                    file.chmod(0o644)
            workspace.chmod(0o755)
            (workspace / "sonny").chmod(0o755)
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            result = run_container(workspace)
            assert hashlib.sha256(source_path.read_bytes()).hexdigest() == digest
            if result.returncode in (125, 126, 127):
                raise RuntimeError("Docker infrastructure failed")
            results[name] = {"exit_code": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()}
            if name == "baseline":
                assert result.returncode == 1 and "FAIL" in result.stderr, "baseline must fail functionally"
            else:
                assert result.returncode == 0, "candidate did not pass isolated functional tests"
    print(json.dumps({"trial": "live-gemini-isolated-functional", "model_response_sha256": staged["model_response_sha256"], "candidate_sha256": staged["sha256"], "results": results, "commit_allowed": False, "independently_verified": False}, sort_keys=True))


if __name__ == "__main__":
    main()
