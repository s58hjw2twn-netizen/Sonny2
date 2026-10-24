"""Transport-neutral model adapter. No HTTP client or credentials are bundled.

Only a separately approved server-side transport can supply model responses.
The factory in inference_config intentionally does not instantiate this adapter.
"""
from dataclasses import dataclass
from typing import Callable

from sonny_one.inference import Request, Response


@dataclass(frozen=True)
class ModelEndpoint:
    model_id: str
    max_output_chars: int = 16000

    def __post_init__(self):
        if not isinstance(self.model_id, str) or not self.model_id.strip() or len(self.model_id) > 128:
            raise ValueError("Invalid model identifier")
        if isinstance(self.max_output_chars, bool) or not isinstance(self.max_output_chars, int) or not 1 <= self.max_output_chars <= 16000:
            raise ValueError("Invalid output limit")


class TransportAdapter:
    """Transport callback is supplied by a separately reviewed server-side caller."""

    def __init__(self, endpoint: ModelEndpoint, transport: Callable[[str, float], str]):
        if not callable(transport):
            raise TypeError("Transport must be callable")
        self._endpoint = endpoint
        self._transport = transport

    def generate(self, request: Request) -> Response:
        if not isinstance(request, Request):
            raise TypeError("Expected validated inference request")
        output = self._transport(request.prompt, request.timeout_seconds)
        if not isinstance(output, str) or not output.strip() or len(output) > self._endpoint.max_output_chars:
            raise ValueError("Invalid transport response")
        return Response(text=output, model_id=self._endpoint.model_id, demo=False)
