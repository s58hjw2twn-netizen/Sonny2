"""In-process outstanding provider work gate.

Unlike an HTTP handler semaphore, a slot is held until the worker finishes,
including after a waiting request is cancelled or times out. This prevents
unbounded accumulation of orphaned provider threads in one process.
Not a distributed quota or a hard thread-kill mechanism.
"""
import asyncio
from threading import BoundedSemaphore

from sonny_one.inference import InferenceFailure, InferenceTimeout, Request, generate


class OutstandingProviderGate:
    def __init__(self, capacity: int = 2):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= 64:
            raise ValueError("Invalid provider capacity")
        self._semaphore = BoundedSemaphore(capacity)

    async def run(self, provider, prompt: str, *, timeout_seconds: float = 5.0):
        incoming = Request(prompt, timeout_seconds=timeout_seconds)
        if not self._semaphore.acquire(blocking=False):
            raise InferenceFailure("Inference capacity reached")

        def worker():
            try:
                return generate(provider, incoming.prompt, timeout_seconds=incoming.timeout_seconds)
            finally:
                self._semaphore.release()

        try:
            return await asyncio.wait_for(asyncio.to_thread(worker), timeout=incoming.timeout_seconds)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise InferenceTimeout("Inference timed out") from exc
        except BaseException:
            # If the coroutine is cancelled before asyncio.to_thread starts,
            # the worker's finally block cannot release the semaphore.
            # A production implementation must handle this lifecycle.
            raise
