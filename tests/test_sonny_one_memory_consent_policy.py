import unittest
from datetime import datetime, timedelta, timezone

from sonny_one.memory_consent_policy import authorize_memory_action


class MemoryConsentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 24, tzinfo=timezone.utc)
        self.valid = dict(
            owner_authenticated=True, explicit_consent=True,
            owner_id="owner-a", memory_owner_id="owner-a",
            consent_expires_at=self.now + timedelta(minutes=5), now=self.now,
        )

    def test_save_with_current_consent(self):
        result = authorize_memory_action("save", **self.valid)
        self.assertTrue(result.allowed)
        self.assertFalse(result.storage_performed)

    def test_recall_with_current_consent(self):
        self.assertTrue(authorize_memory_action("recall", **self.valid).allowed)

    def test_missing_consent_rejected(self):
        self.assertFalse(authorize_memory_action("save", **{**self.valid, "explicit_consent": False}).allowed)

    def test_missing_expiry_rejected(self):
        self.assertFalse(authorize_memory_action("recall", **{**self.valid, "consent_expires_at": None}).allowed)

    def test_expired_consent_rejected(self):
        self.assertFalse(authorize_memory_action("save", **{**self.valid, "consent_expires_at": self.now}).allowed)

    def test_cross_owner_rejected(self):
        self.assertFalse(authorize_memory_action("recall", **{**self.valid, "memory_owner_id": "owner-b"}).allowed)

    def test_unauthenticated_rejected(self):
        self.assertFalse(authorize_memory_action("delete", **{**self.valid, "owner_authenticated": False}).allowed)

    def test_owner_can_delete_without_consent(self):
        result = authorize_memory_action("delete", **{**self.valid, "explicit_consent": False})
        self.assertTrue(result.allowed)
        self.assertFalse(result.storage_performed)

    def test_unknown_action_rejected(self):
        self.assertFalse(authorize_memory_action("export", **self.valid).allowed)

    def test_naive_expiry_rejected(self):
        self.assertFalse(authorize_memory_action("save", **{**self.valid, "consent_expires_at": datetime(2026, 10, 25)}).allowed)


if __name__ == "__main__":
    unittest.main()
