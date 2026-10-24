"""Gemini free-tier response parser; deliberately no HTTP, credentials or activation.

Transport and endpoint configuration must be reviewed separately. Never put
provider keys in GitHub Pages or client-side JavaScript.
"""
from sonny_one.inference import Response


def parse_gemini_response(payload: object, *, model_id: str = "gemini-2.5-flash-lite") -> Response:
    if not isinstance(payload, dict):
        raise ValueError("Invalid model response")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("No model response")
    candidate = candidates[0]
    if not isinstance(candidate, dict) or candidate.get("finishReason") != "STOP":
        raise ValueError("Model response incomplete")
    content = candidate.get("content")
    if not isinstance(content, dict):
        raise ValueError("Invalid model content")
    parts = content.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("No model text")
    texts = []
    for part in parts:
        if not isinstance(part, dict) or not isinstance(part.get("text"), str):
            raise ValueError("Unsupported model part")
        texts.append(part["text"])
    result = "".join(texts)
    if not result.strip() or len(result) > 16000:
        raise ValueError("Invalid model output")
    if not isinstance(model_id, str) or not model_id.strip() or len(model_id) > 128:
        raise ValueError("Invalid model identifier")
    return Response(text=result, model_id=model_id, demo=False)
