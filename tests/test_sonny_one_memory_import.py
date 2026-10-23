import json
import unittest
from sonny_one.life_memory import LifeMemory
from sonny_one.memory_policy import MemoryCandidate, MemoryStatus
from sonny_one.memory_export import export_active_memories
from sonny_one.memory_import import import_active_memories

class MemoryImportTests(unittest.TestCase):
    def setUp(self):
        self.memory = LifeMemory(":memory:")
        self.memory.add(MemoryCandidate(
            "alice", "user-confirmed", "Prefers concise answers",
            MemoryStatus.VALIDATED, 1.0, True))
        self.payload = export_active_memories(self.memory, "alice")

    def test_round_trip_to_new_account(self):
        self.assertEqual(import_active_memories(
            self.memory, "bob", self.payload, consent=True), 1)
        self.assertEqual(self.memory.recall("bob")[0].statement,
                         "Prefers concise answers")

    def test_no_consent(self):
        with self.assertRaises(ValueError):
            import_active_memories(self.memory, "bob", self.payload, consent=False)

    def test_atomic_validation(self):
        obj = json.loads(self.payload)
        obj["records"].append({"statement": "", "source": "x",
                               "confidence": 1, "valid_until": None})
        with self.assertRaises(ValueError):
            import_active_memories(self.memory, "bob", json.dumps(obj), consent=True)
        self.assertEqual(self.memory.recall("bob"), [])

    def test_unknown_version(self):
        obj = json.loads(self.payload)
        obj["version"] = 2
        with self.assertRaises(ValueError):
            import_active_memories(self.memory, "bob", json.dumps(obj), consent=True)

    def test_expired_record(self):
        obj = json.loads(self.payload)
        obj["records"][0]["valid_until"] = "2020-01-01T00:00:00Z"
        with self.assertRaises(ValueError):
            import_active_memories(self.memory, "bob", json.dumps(obj), consent=True)

    def test_nonfinite_confidence(self):
        obj = json.loads(self.payload)
        obj["records"][0]["confidence"] = float("nan")
        with self.assertRaises(ValueError):
            import_active_memories(self.memory, "bob", json.dumps(obj), consent=True)

if __name__ == "__main__":
    unittest.main()
