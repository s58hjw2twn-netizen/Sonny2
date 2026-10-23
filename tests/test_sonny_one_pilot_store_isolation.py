"""Offline account-isolation tests for the existing pilot persistence layer.

These tests use only synthetic accounts and temporary files. They do not
authorize the SQLite pilot store for production or internet-facing use.
"""
import tempfile
import unittest
from pathlib import Path
from sonny_one.pilot_store import PilotStore

class PilotStoreIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = PilotStore(Path(self.tmp.name) / "pilot.db")
        self.alice = self.store.create_user("alice", "test-password-123")
        self.bob = self.store.create_user("bob", "test-password-456")

    def test_workspaces_are_isolated(self):
        self.store.set_goal(self.alice, "Alice goal")
        self.store.set_goal(self.bob, "Bob goal")
        self.assertEqual(self.store.workspace(self.alice)["goal"], "Alice goal")
        self.assertEqual(self.store.workspace(self.bob)["goal"], "Bob goal")

    def test_memories_cannot_be_deleted_cross_account(self):
        fact = self.store.save_fact(self.alice, "Alice's private fact")
        self.assertFalse(self.store.forget_fact(self.bob, fact))
        self.assertEqual(len(self.store.workspace(self.alice)["memories"]), 1)
        self.assertEqual(self.store.workspace(self.bob)["memories"], [])

    def test_corrections_cannot_cross_accounts(self):
        fact = self.store.save_fact(self.alice, "Original")
        self.assertEqual(self.store.correct_fact(self.bob, fact, "Tampered", 1), "missing")
        self.assertEqual(self.store.workspace(self.alice)["memories"][0]["statement"], "Original")

    def test_session_owner_binding_and_revocation(self):
        self.store.add_session(self.alice, "synthetic-session", 9999999999)
        self.assertTrue(self.store.session_valid(self.alice, "synthetic-session"))
        self.assertFalse(self.store.session_valid(self.bob, "synthetic-session"))
        self.store.revoke_session("synthetic-session")
        self.assertFalse(self.store.session_valid(self.alice, "synthetic-session"))

    def test_chat_history_isolated(self):
        def fake_reply(message, goal, memories):
            return {"text": "synthetic reply"}
        self.store.reply(self.alice, "Private chat", "request-alice", fake_reply)
        self.assertEqual(len(self.store.workspace(self.alice)["messages"]), 2)
        self.assertEqual(self.store.workspace(self.bob)["messages"], [])

    def test_erase_does_not_affect_other_user(self):
        self.store.save_fact(self.alice, "Keep Alice")
        self.store.save_fact(self.bob, "Erase Bob")
        self.store.erase(self.bob)
        self.assertEqual(len(self.store.workspace(self.alice)["memories"]), 1)
        self.assertEqual(self.store.workspace(self.bob)["memories"], [])

if __name__ == "__main__":
    unittest.main()
