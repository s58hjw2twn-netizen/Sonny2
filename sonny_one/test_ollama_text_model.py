"""No-network tests for the opt-in Ollama text model bridge."""
import unittest
from unittest.mock import patch

from sonny_one.inference import Response
from sonny_one.model_router import ModelOption, ModelRouter
from sonny_one.ollama_text_model import OllamaTextModel


class OllamaTextModelTests(unittest.TestCase):
    def test_construct_does_not_contact_server(self):
        with patch("sonny_one.ollama_local.build_opener") as opener:
            model = OllamaTextModel("test:1b")
            opener.assert_called_once()
            self.assertEqual(model._provider.model, "test:1b")

    def test_router_default_denies_model_without_owner_approval(self):
        model = OllamaTextModel("test:1b")
        router = ModelRouter([ModelOption("test:1b", model, frozenset({"chat"}))])
        with self.assertRaises(LookupError):
            router.generate("chat", system="safe", user="hello")

    def test_explicitly_authorized_route_with_mock_response(self):
        model = OllamaTextModel("test:1b")
        option = ModelOption("test:1b", model, frozenset({"chat"}),
                             approved=True, license_verified=True, available=True)
        router = ModelRouter([option])
        with patch.object(model._provider, "generate",
                          return_value=Response("Local reply", "test:1b", demo=False)) as call:
            self.assertEqual(router.generate("chat", system="Be concise", user="Hello"),
                             ("Local reply", "test:1b"))
        prompt = call.call_args.args[0].prompt
        self.assertIn("Be concise", prompt)
        self.assertIn("Hello", prompt)

    def test_input_limits(self):
        model = OllamaTextModel("test:1b")
        for system, user in (("x" * 2001, "hello"), ("ok", "x" * 4001), ("ok", " ")):
            with self.assertRaises(ValueError):
                model.generate(system=system, user=user)


if __name__ == "__main__":
    unittest.main()
