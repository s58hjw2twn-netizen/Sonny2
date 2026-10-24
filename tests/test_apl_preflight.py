"""Offline preflight checks never execute a candidate or run a container."""
import subprocess
import unittest
from sonny_one.apl.preflight import check_host


class PreflightTests(unittest.TestCase):
    def test_missing_docker_fails_closed(self):
        result = check_host(which=lambda _: None)
        self.assertFalse(result["ready_for_containment_validation"])
        self.assertFalse(result["hostile_code_execution_approved"])

    def test_unpinned_image_fails_even_with_running_daemon(self):
        def fake_run(args, **kwargs):
            value = '["name=rootless"]' if ".SecurityOptions" in args[-1] else "27.0"
            return subprocess.CompletedProcess(args, 0, value, "")
        result = check_host("runner:latest", which=lambda _: "/usr/bin/docker", run=fake_run)
        self.assertFalse(result["ready_for_containment_validation"])

    def test_rootful_daemon_not_accepted(self):
        def fake_run(args, **kwargs):
            value = "[]" if ".SecurityOptions" in args[-1] else "27.0"
            return subprocess.CompletedProcess(args, 0, value, "")
        result = check_host(which=lambda _: "/usr/bin/docker", run=fake_run)
        self.assertFalse(result["ready_for_containment_validation"])

    def test_verified_local_digest_only_enables_validation(self):
        image = "runner@sha256:" + "a" * 64
        def fake_run(args, **kwargs):
            if "inspect" in args:
                value = '["' + image + '"]'
            elif ".SecurityOptions" in args[-1]:
                value = '["name=rootless"]'
            else:
                value = "27.0"
            return subprocess.CompletedProcess(args, 0, value, "")
        result = check_host(image, which=lambda _: "/usr/bin/docker", run=fake_run)
        self.assertTrue(result["ready_for_containment_validation"])
        self.assertFalse(result["hostile_code_execution_approved"])
