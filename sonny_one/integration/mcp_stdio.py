"""Local-only, newline-delimited JSON-RPC transport for Sonny's read-only MCP prototype.

No network listener, credentials, memory access, repository writes, or
autonomous development. Intended for local integration tests only.
"""
from __future__ import annotations

import json
import sys

from sonny_one.integration.mcp_protocol import handle_message

MAX_MESSAGE_BYTES = 65536


def serve_stream(input_stream, output_stream) -> None:
    for raw in input_stream:
        if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
            continue  # Reject oversized input without echoing untrusted content.
        try:
            message = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        response = handle_message(message)
        if response is not None:
            output_stream.write(json.dumps(response, separators=(",", ":")) + "\n")
            output_stream.flush()


def main() -> None:
    serve_stream(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
