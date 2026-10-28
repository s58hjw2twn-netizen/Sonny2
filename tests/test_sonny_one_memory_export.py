import json
import unittest
from sonny_one.life_memory import LifeMemory
from sonny_one.memory_policy import MemoryCandidate, MemoryStatus
from sonny_one.memory_export import export_active_memories

class MemoryExportTests(unittest.TestCase):
    def test_only_requested_user(self):
        memory = LifeMemory(":memory:")
        for user, value in (("a", "tea"), ("b", "private")):
            memory.add(MemoryCandidate(user, "confirmed", value,
                                       MemoryStatus.VALIDATED, 1.0, True))
        payload = export_active_memories(memory, "a")
        self.assertEqual(json.loads(payload)["records"][0]["statement"], "tea")
        self.assertNotIn("private", payload)
        self.assertEqual(json.loads(payload)["version"], 1)

    def test_revoked_excluded(self):
        memory = LifeMemory(":memory:")
        rid = memory.add(MemoryCandidate("a", "confirmed", "old",
                                         MemoryStatus.VALIDATED, 1.0, True))
        memory.revoke("a", rid)
        self.assertEqual(json.loads(export_active_memories(memory, "a"))["records"], [])

    def test_empty_user_rejected(self):
        with self.assertRaises(ValueError):
            export_active_memories(LifeMemory(":memory:"), "")

if __name__ == "__main__":
    unittest.main()
