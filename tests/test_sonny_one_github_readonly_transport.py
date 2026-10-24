import io
import json
import unittest
from unittest.mock import patch

from sonny_one.development_controller.github_readonly_transport import github_readonly_json

BASE = "https://api.github.com/repos/s58hjw2twn-netizen/Sonny2"


class FakeResponse:
    def __init__(self, payload):
        self.data = io.BytesIO(json.dumps(payload).encode())

    def read(self, n):
        return self.data.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class GitHubTransportTests(unittest.TestCase):
    def test_allowed_commit_read(self):
        class Opener:
            def open(self, request, timeout):
                self.request = request
                return FakeResponse({"sha": "a" * 40})
        opener = Opener()
        with patch("sonny_one.development_controller.github_readonly_transport.build_opener",
                   return_value=opener):
            value = github_readonly_json(BASE + "/commits/" + "a" * 40)
        self.assertEqual(value["sha"], "a" * 40)
        self.assertEqual(opener.request.get_method(), "GET")

    def test_allowed_run_read(self):
        class Opener:
            def open(self, request, timeout):
                return FakeResponse({"id": 101})
        with patch("sonny_one.development_controller.github_readonly_transport.build_opener",
                   return_value=Opener()):
            self.assertEqual(github_readonly_json(BASE + "/actions/runs/101")["id"], 101)

    def test_allowlisted_branch_head_read(self):
        class Opener:
            def open(self, request, timeout):
                return FakeResponse({"commit": {"sha": "a" * 40}})
        with patch("sonny_one.development_controller.github_readonly_transport.build_opener",
                   return_value=Opener()):
            value = github_readonly_json(BASE + "/branches/research/apl-001")
        self.assertEqual(value["commit"]["sha"], "a" * 40)

    def test_external_url_rejected(self):
        with self.assertRaises(ValueError):
            github_readonly_json("https://example.com/")

    def test_query_string_rejected(self):
        with self.assertRaises(ValueError):
            github_readonly_json(BASE + "/actions/runs/101?redirect=1")

    def test_other_repository_rejected(self):
        with self.assertRaises(ValueError):
            github_readonly_json("https://api.github.com/repos/other/repo/actions/runs/101")

    def test_bad_timeout_rejected(self):
        with self.assertRaises(ValueError):
            github_readonly_json(BASE + "/actions/runs/101", timeout=0)

    def test_redirect_handler_rejects(self):
        from sonny_one.development_controller.github_readonly_transport import HTTPRedirectHandler
        class Opener:
            def open(self, request, timeout):
                return FakeResponse({"id": 101})
        with patch("sonny_one.development_controller.github_readonly_transport.build_opener",
                   side_effect=lambda handler: (self.assertIsInstance(handler, HTTPRedirectHandler), Opener())[1]):
            self.assertEqual(github_readonly_json(BASE + "/actions/runs/101")["id"], 101)


if __name__ == "__main__":
    unittest.main()
