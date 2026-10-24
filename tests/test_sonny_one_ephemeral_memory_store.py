import unittest
from datetime import datetime, timedelta, timezone
from sonny_one.ephemeral_memory_store import EphemeralMemoryStore


class EphemeralMemoryTests(unittest.TestCase):
    def setUp(self):
        self.store = EphemeralMemoryStore()
        self.now = datetime(2026, 10, 24, tzinfo=timezone.utc)
        self.consent = self.now + timedelta(hours=1)
        self.args = dict(owner_id="alice", owner_authenticated=True,
                         explicit_consent=True, consent_expires_at=self.consent,
                         now=self.now)

    def test_save_and_recall(self):
        key = self.store.save("  My preferred theme  ", **self.args)
        self.assertEqual(self.store.recall(key, **self.args), "My preferred theme")

    def test_cross_owner_is_hidden(self):
        key = self.store.save("private", **self.args)
        with self.assertRaises(KeyError):
            self.store.recall(key, **{**self.args, "owner_id": "bob"})
        with self.assertRaises(KeyError):
            self.store.delete(key, owner_id="bob", owner_authenticated=True)

    def test_no_save_without_consent(self):
        with self.assertRaises(PermissionError):
            self.store.save("private", **{**self.args, "explicit_consent": False})

    def test_no_recall_after_consent_expires(self):
        key = self.store.save("private", **self.args)
        with self.assertRaises(PermissionError):
            self.store.recall(key, **{**self.args, "now": self.consent})

    def test_owner_can_delete_after_consent_expires(self):
        key = self.store.save("private", **self.args)
        self.store.delete(key, owner_id="alice", owner_authenticated=True)
        with self.assertRaises(KeyError):
            self.store.recall(key, **self.args)

    def test_unauthenticated_deletion_denied(self):
        key = self.store.save("private", **self.args)
        with self.assertRaises(PermissionError):
            self.store.delete(key, owner_id="alice", owner_authenticated=False)

    def test_reject_oversized_record(self):
        with self.assertRaises(ValueError):
            self.store.save("x" * 501, **self.args)

    def test_clear_discards_records(self):
        key = self.store.save("private", **self.args)
        self.store.clear()
        with self.assertRaises(KeyError):
            self.store.recall(key, **self.args)


if __name__ == "__main__":
    unittest.main()
