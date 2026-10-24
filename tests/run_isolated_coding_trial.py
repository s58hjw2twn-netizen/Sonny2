"""Deterministic, isolated functional trial for the coding-model pipeline.

Uses a simulated Gemini transport: this does NOT claim a live provider call.
Designed for GitHub-hosted Linux runners with Docker installed.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

import httpx

from sonny.coding_model_provider import generate_and_stage_patch
from sonny.research_agent import Task


class StubClient:
    def post(self, url, **kwargs):
        response = json.dumps({
            "path": "sonny/example.py",
            "content": "def add(a, b):\n    return a + b\n",
            "reason": "Repair the addition function",
        })
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": response}]}}]},
            request=httpx.Request("POST", url),
        )


def run_container(workspace: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "docker", "run", "--rm", "--pull", "never",
            "--network", "none", "--read-only", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "64",
            "--memory", "256m", "--cpus", "1", "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,nosuid,noexec,size=16m",
            "--mount", f"type=bind,source={workspace},target=/workspace,readonly",
            "--workdir", "/workspace", "python:3.11-slim",
            "python", "-B", "-m", "unittest", "-q", "test_example",
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )


def main():
    os.environ["GEMINI_API_KEY"] = "simulated-provider-only"
    source = "def add(a, b):\n    return a - b\n"
    task = Task("FUNCTIONAL1", "Repair addition", ("sonny/example.py",), "low")
    staged = generate_and_stage_patch(task, {"sonny/example.py": source}, client=StubClient())
    assert staged["commit_allowed"] is False
    assert staged["independently_verified"] is False
    test = (
        "import unittest\n"
        "from sonny.example import add\n"
        "class ExampleTest(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n"
    )
    with tempfile.TemporaryDirectory(prefix="sonny-isolated-") as root:
        results = []
        for name, candidate in (
            ("baseline", source),
            ("candidate", staged["candidate"]["sonny/example.py"]),
        ):
            workspace = Path(root) / name
            (workspace / "sonny").mkdir(parents=True)
            (workspace / "sonny" / "__init__.py").write_text("")
            (workspace / "sonny" / "example.py").write_text(candidate)
            (workspace / "test_example.py").write_text(test)
            for file in workspace.rglob("*"):
                if file.is_file():
                    file.chmod(0o644)
            workspace.chmod(0o755)
            (workspace / "sonny").chmod(0o755)
            result = run_container(workspace)
            print(f"{name}: exit={result.returncode}; output={result.stdout[-500:]} {result.stderr[-500:]}")
            if result.returncode in (125, 126, 127):
                raise RuntimeError("Docker infrastructure failure")
            if name == "baseline" and "FAIL" not in result.stderr:
                raise AssertionError("baseline failure must be a unittest assertion")
            results.append(result.returncode)
        assert results[0] == 1, "baseline must fail as a test failure (not Docker infrastructure)"
        assert results[1] == 0, "candidate must pass the functional test"
    print("PASS: isolated functional repair; no commit authority granted")


if __name__ == "__main__":
    main()
