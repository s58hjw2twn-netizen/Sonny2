"""Safety tests for opt-in model orchestration."""
import unittest

from sonny_one.model_router import ModelOption, ModelRouter


class FakeModel:
    def generate(self, *, system, user):
        return "reply"


class RouterSafetyTests(unittest.TestCase):
    def test_default_model_not_authorized(self):
        router = ModelRouter([ModelOption("local", FakeModel(), frozenset({"chat"}))])
        with self.assertRaises(LookupError):
            router.select("chat")

    def test_explicitly_approved_local_model(self):
        option = ModelOption("local", FakeModel(), frozenset({"chat"}),
                             approved=True, license_verified=True, available=True)
        router = ModelRouter([option])
        self.assertEqual(router.generate("chat", system="safe", user="hello"),
                         ("reply", "local"))

    def test_cloud_model_not_silently_selected(self):
        option = ModelOption("cloud", FakeModel(), frozenset({"chat"}),
                             approved=True, license_verified=True, available=True,
                             local=False)
        with self.assertRaises(LookupError):
            ModelRouter([option]).select("chat")

    def test_invalid_cost_rejected(self):
        with self.assertRaises(ValueError):
            ModelRouter([ModelOption("x", FakeModel(), frozenset({"chat"}),
                                     estimated_cost_units=True)])


if __name__ == "__main__":
    unittest.main()
