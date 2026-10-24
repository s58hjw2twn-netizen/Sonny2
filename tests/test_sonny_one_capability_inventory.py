import unittest
from sonny_one.capability_inventory import (
    CAPABILITIES, capability_inventory, capability_status, execution_allowed
)


class CapabilityInventoryTests(unittest.TestCase):
    def test_all_six_roadmap_modules_present(self):
        self.assertEqual(len(CAPABILITIES), 6)
        self.assertEqual(len({c.name for c in CAPABILITIES}), 6)

    def test_no_capability_claims_to_be_live(self):
        self.assertTrue(all(c.status in ("prototype", "planned") for c in CAPABILITIES))

    def test_external_execution_fails_closed(self):
        for capability in CAPABILITIES:
            with self.subTest(capability=capability.name):
                self.assertFalse(execution_allowed(capability.name))

    def test_unknown_capability_rejected(self):
        with self.assertRaises(KeyError):
            capability_status("imaginary")

    def test_inventory_is_serializable_data(self):
        import json
        self.assertEqual(len(json.loads(json.dumps(capability_inventory()))), 6)


if __name__ == "__main__":
    unittest.main()
