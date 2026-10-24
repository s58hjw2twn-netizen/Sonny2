"""Private provider activation contract tests; no network or real model."""
import unittest
from sonny_one.private_provider import get_private_provider, install_private_provider, reset_private_provider
from sonny_one.inference import Request, Response


class FakeProvider:
    def generate(self, request: Request) -> Response:
        return Response(text="mock answer", model_id="mock", demo=False)


class PrivateProviderTests(unittest.TestCase):
    def tearDown(self):
        reset_private_provider()

    def test_default_offline(self):
        reset_private_provider()
        self.assertTrue(get_private_provider().generate(Request("hello")).demo)

    def test_activation_requires_explicit_flag(self):
        with self.assertRaises(PermissionError):
            install_private_provider(FakeProvider())
        self.assertTrue(get_private_provider().generate(Request("hello")).demo)

    def test_approved_mock_and_reset(self):
        install_private_provider(FakeProvider(), approved=True)
        self.assertEqual(get_private_provider().generate(Request("hello")).text, "mock answer")
        reset_private_provider()
        self.assertTrue(get_private_provider().generate(Request("hello")).demo)

    def test_rejects_invalid_provider(self):
        with self.assertRaises(TypeError):
            install_private_provider(object(), approved=True)


if __name__ == "__main__":
    unittest.main()
