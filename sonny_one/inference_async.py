"""Bounded async inference orchestration for the local prototype.

A deadline limits how long a caller waits. It does NOT terminate a running
blocking provider; providers must implement their own network/read timeouts.
No external provider is configured or invoked by this module.
"""
import asyncio

from sonny_one.inference import InferenceTimeout, Request, Response, generate


async def generate_with_deadline(provider, prompt: str, *, timeout_seconds: float = 20.0) -> Response:
    request = Request(prompt, timeout_seconds=timeout_seconds)
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(generate, provider, request.prompt),
            timeout=request.timeout_seconds,
        )
    except (TimeoutError, asyncio.TimeoutError) as exc:
        raise InferenceTimeout("Inference timed out") from exc
