"""Security regression tests: Ollama HTTP must never inherit proxy settings."""
import unittest
from unittest.mock import patch

from urllib.request import ProxyHandler

from sonny_one.development_controller.ollama_proposal_producer import OllamaProposalProducer
from sonny_one.development_controller.local_model_preflight import check_local_model


class LocalProxyIsolationTests(unittest.TestCase):
    def test_inference_disables_environment_proxy(self):
        captured = []

        def inspect(*handlers):
            captured.extend(handlers)
            raise RuntimeError("request intercepted")

        task = {"id": "RES-001", "state": "ready", "requires_approval": False}
        with patch("sonny_one.development_controller.ollama_proposal_producer.build_opener",
                   side_effect=inspect):
            with self.assertRaises(RuntimeError):
                OllamaProposalProducer(model="local", enabled=True)(task)
        self.assertTrue(any(isinstance(h, ProxyHandler) and h.proxies == {}
                            for h in captured))

    def test_discovery_disables_environment_proxy(self):
        captured = []

        def inspect(*handlers):
            captured.extend(handlers)
            raise RuntimeError("request intercepted")

        with patch("sonny_one.development_controller.local_model_preflight.build_opener",
                   side_effect=inspect):
            with self.assertRaises(RuntimeError):
                check_local_model("local", enabled=True)
        self.assertTrue(any(isinstance(h, ProxyHandler) and h.proxies == {}
                            for h in captured))


if __name__ == "__main__":
    unittest.main()
