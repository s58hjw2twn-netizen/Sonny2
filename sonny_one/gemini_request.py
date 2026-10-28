"""Fail-closed Gemini request construction, with no network or credential access.

Only a separately approved server-side transport may send this payload.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class GeminiRequestConfig:
    model_id: str = "gemini-2.5-flash-lite"
    max_output_tokens: int = 256
    temperature: float = 0.4

    def __post_init__(self):
        if not isinstance(self.model_id, str) or not self.model_id.strip() or len(self.model_id) > 128:
            raise ValueError("Invalid model identifier")
        if isinstance(self.max_output_tokens, bool) or not isinstance(self.max_output_tokens, int) or not 1 <= self.max_output_tokens <= 512:
            raise ValueError("Invalid output token cap")
        if isinstance(self.temperature, bool) or not isinstance(self.temperature, (int, float)) or not math.isfinite(self.temperature) or not 0 <= self.temperature <= 1:
            raise ValueError("Invalid temperature")


def build_gemini_request(message: str, config: GeminiRequestConfig = GeminiRequestConfig()) -> dict:
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        raise ValueError("Invalid message")
    if not isinstance(config, GeminiRequestConfig):
        raise TypeError("Invalid request configuration")
    return {
        "contents": [{"role": "user", "parts": [{"text": message.strip()}]}],
        "generationConfig": {
            "maxOutputTokens": config.max_output_tokens,
            "temperature": config.temperature,
        },
    }
