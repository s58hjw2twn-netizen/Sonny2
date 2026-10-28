"""Candidate archive validation rejects traversal, links, duplicates, and bombs."""
import io
import tarfile
import unittest
from sonny_one.apl.candidate_archive import validate_candidate_tarball


def tar_bytes(entries):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tf:
        for name, kind, payload in entries:
            info = tarfile.TarInfo(name)
            if kind == "dir":
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
            elif kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "../../private"
                tf.addfile(info)
            else:
                info.size = len(payload)
                tf.addfile(info, io.BytesIO(payload))
    return out.getvalue()


class CandidateArchiveTests(unittest.TestCase):
    def test_regular_archive_validated_without_execution(self):
        result = validate_candidate_tarball(tar_bytes([
            ("src", "dir", b""), ("src/module.py", "file", b"x=1")]))
        self.assertTrue(result["valid"])
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["holdout_access"])
        self.assertEqual(result["promotion"], "FORBIDDEN")

    def test_traversal_absolute_links_and_duplicates_rejected(self):
        cases = [
            [("../escape.py", "file", b"x")],
            [("/absolute.py", "file", b"x")],
            [("src/link", "symlink", b"")],
            [("src/a.py", "file", b"a"), ("src/a.py", "file", b"b")],
        ]
        for entries in cases:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                validate_candidate_tarball(tar_bytes(entries))

    def test_archive_size_limits(self):
        with self.assertRaises(ValueError):
            validate_candidate_tarball(b"x" * 30, max_bytes=10)


if __name__ == "__main__":
    unittest.main()
