"""APL-001 policy tests: no network, model or Docker needed."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from sonny_one.apl.policy import append_lineage, validate_patch, verify_lineage

GOOD = """diff --git a/sonny_one/apl_targets/example.py b/sonny_one/apl_targets/example.py
--- a/sonny_one/apl_targets/example.py
+++ b/sonny_one/apl_targets/example.py
@@ -1 +1 @@
-old
+new
"""


class TestPatchPolicy(unittest.TestCase):
    def test_experimental_patch_allowed(self):
        self.assertEqual(validate_patch(GOOD), ["sonny_one/apl_targets/example.py"])

    def test_production_patch_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace("sonny_one/apl_targets/", "sonny/"))

    def test_frozen_baseline_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace("sonny_one/apl_targets/", "research/frozen/"))

    def test_traversal_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace("apl_targets/example.py", "apl_targets/../example.py"))

    def test_rename_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace(" b/sonny_one/apl_targets/example.py",
                                        " b/sonny_one/apl_targets/other.py", 1))

    def test_symlink_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD + "new file mode 120000\n")

    def test_duplicate_diff_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD + GOOD)

    def test_oversize_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD + ("x" * 140000))

    def test_lineage_chain_detects_tampering(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            append_lineage(ledger, {"candidate": "c1", "result": "REJECTED"})
            append_lineage(ledger, {"candidate": "c2", "result": "PASS"})
            self.assertTrue(verify_lineage(ledger))
            lines = ledger.read_text().splitlines()
            first = json.loads(lines[0])
            first["result"] = "PASS"
            lines[0] = json.dumps(first)
            ledger.write_text("\n".join(lines) + "\n")
            self.assertFalse(verify_lineage(ledger))


    def test_corrupted_lineage_cannot_be_extended(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            append_lineage(ledger, {"candidate": "c1"})
            entry = json.loads(ledger.read_text().splitlines()[0])
            entry["candidate"] = "altered"
            ledger.write_text(json.dumps(entry) + "\n")
            with self.assertRaises(ValueError):
                append_lineage(ledger, {"candidate": "c2"})

    def test_reserved_lineage_fields_rejected(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            with self.assertRaises(ValueError):
                append_lineage(ledger, {"previous_hash": "forged"})
            with self.assertRaises(ValueError):
                append_lineage(ledger, {"record_hash": "forged"})


    def test_non_experimental_second_diff_denied(self):
        patch = GOOD + GOOD.replace("sonny_one/apl_targets/", "sonny/")
        with self.assertRaises(ValueError):
            validate_patch(patch)

    def test_dot_component_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace("apl_targets/example.py", "apl_targets/./example.py"))

    def test_empty_patch_denied(self):
        with self.assertRaises(ValueError):
            validate_patch("")

    def test_binary_patch_denied(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD + "GIT binary patch\\n")

    def test_lineage_rejects_appending_after_tamper(self):
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            append_lineage(ledger, {"candidate": "first"})
            data = ledger.read_text()
            ledger.write_text(data.replace("first", "altered"))
            with self.assertRaises(ValueError):
                append_lineage(ledger, {"candidate": "second"})


    def test_spoofed_original_header_rejected(self):
        patch = GOOD.replace("--- a/sonny_one/apl_targets/example.py",
                             "--- a/sonny_one/private.py")
        with self.assertRaises(ValueError):
            validate_patch(patch)

    def test_spoofed_destination_header_rejected(self):
        patch = GOOD.replace("+++ b/sonny_one/apl_targets/example.py",
                             "+++ b/sonny_one/private.py")
        with self.assertRaises(ValueError):
            validate_patch(patch)

    def test_missing_unified_header_rejected(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD.replace("+++ b/sonny_one/apl_targets/example.py" + chr(10), ""))

    def test_executable_mode_change_rejected(self):
        with self.assertRaises(ValueError):
            validate_patch(GOOD + "new mode 100755\\n")


if __name__ == "__main__":
    unittest.main()
