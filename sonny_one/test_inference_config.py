"""No external model can be enabled by a flag alone."""
import unittest
from sonny_one.inference import OfflineProvider
from sonny_one.inference_config import InferenceSettings, ProviderNotApproved, build_provider


class InferenceConfigTests(unittest.TestCase):
    def test_default_offline(self):
        self.assertIsInstance(build_provider(InferenceSettings()), OfflineProvider)

    def test_external_disabled(self):
        with self.assertRaises(ProviderNotApproved):
            build_provider(InferenceSettings(provider="external"))

    def test_external_flag_does_not_enable_unreviewed_adapter(self):
        with self.assertRaises(ProviderNotApproved):
            build_provider(InferenceSettings(provider="external", allow_external=True))

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):
            InferenceSettings(provider="unknown")

    def test_invalid_flag_rejected(self):
        with self.assertRaises(ValueError):
            InferenceSettings(allow_external="true")


if __name__ == "__main__":
    unittest.main()
