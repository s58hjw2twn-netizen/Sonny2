"""Optional Gemini transport. Never expose API keys to browser clients."""
import os
import httpx

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def generate_gemini(instructions, history, message, *, client=None):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    model = os.environ.get("SONNY_GEMINI_MODEL", "gemini-2.5-flash")
    if not model.replace("-", "").replace(".", "").isalnum():
        raise ValueError("Invalid Gemini model name")
    contents = []
    for turn in history or []:
        role = turn.get("role")
        if role not in ("user", "assistant") or not turn.get("content"):
            continue
        contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": turn["content"]}]})
    if not (contents and contents[-1] == {"role": "user", "parts": [{"text": message}]}):
        contents.append({"role": "user", "parts": [{"text": message}]})
    payload = {"systemInstruction": {"parts": [{"text": instructions}]}, "contents": contents, "generationConfig": {"maxOutputTokens": 1200}}
    url = GEMINI_ENDPOINT.format(model=model)
    if client is None:
        with httpx.Client(timeout=45.0) as own_client:
            response = own_client.post(url, headers={"x-goog-api-key": key}, json=payload)
    else:
        response = client.post(url, headers={"x-goog-api-key": key}, json=payload)
    response.raise_for_status()
    data = response.json()
    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    result = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
    if not result:
        raise RuntimeError("Gemini returned no readable response")
    return result
