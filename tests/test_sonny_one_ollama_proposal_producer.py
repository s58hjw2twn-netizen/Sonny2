import io
import json
import unittest
from unittest.mock import patch

from sonny_one.development_controller.ollama_proposal_producer import OllamaProposalProducer


def task():
    return {"id": "RES-001", "state": "ready", "requires_approval": False}


class Response:
    def __init__(self, obj):
        self.stream = io.BytesIO(json.dumps(obj).encode())

    def read(self, n):
        return self.stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class OllamaProducerTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with self.assertRaises(PermissionError):
            OllamaProposalProducer(model="qwen2.5-coder:1.5b")(task())

    def test_rejects_remote_or_invalid_model(self):
        with self.assertRaises(ValueError):
            OllamaProposalProducer(model="http://example.com")

    def test_rejects_nonresearch_task(self):
        producer = OllamaProposalProducer(model="local-model", enabled=True)
        with self.assertRaises(PermissionError):
            producer({**task(), "id": "DEV-001"})

    def test_local_proposal_response(self):
        class Opener:
            def open(self, request, timeout):
                self.request = request
                return Response({"response": json.dumps({
                    "task_id": "RES-001", "patch_text": "diff --git a/x b/x"})})
        opener = Opener()
        with patch("sonny_one.development_controller.ollama_proposal_producer.build_opener",
                   return_value=opener):
            result = OllamaProposalProducer(model="local-model", enabled=True)(task())
        self.assertEqual(result["task_id"], "RES-001")
        self.assertEqual(opener.request.full_url, "http://127.0.0.1:11434/api/generate")
        self.assertEqual(opener.request.get_method(), "POST")

    def test_rejects_extra_model_fields(self):
        class Opener:
            def open(self, request, timeout):
                return Response({"response": json.dumps({
                    "task_id": "RES-001", "patch_text": "x", "command": "sh"})})
        with patch("sonny_one.development_controller.ollama_proposal_producer.build_opener",
                   return_value=Opener()):
            with self.assertRaises(ValueError):
                OllamaProposalProducer(model="local-model", enabled=True)(task())

    def test_rejects_invalid_timeout(self):
        with self.assertRaises(ValueError):
            OllamaProposalProducer(model="local-model", timeout=0)


if __name__ == "__main__":
    unittest.main()
