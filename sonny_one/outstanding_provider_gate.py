"""Bound outstanding synchronous provider work across caller timeouts.

A capacity slot is released only when the worker future actually finishes,
even if the awaiting HTTP handler times out or is cancelled. This prevents
unbounded abandoned provider work within a single process. It does not kill
blocked threads, share quotas across processes, or guarantee zero API cost.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore

from sonny_one.inference import InferenceFailure, InferenceTimeout, Request, generate


class OutstandingProviderGate:
    def __init__(self, capacity: int = 2):
        if isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= 64:
            raise ValueError("Invalid provider capacity")
        self._semaphore = BoundedSemaphore(capacity)
        self._executor = ThreadPoolExecutor(max_workers=capacity, thread_name_prefix="sonny-provider")

    async def run(self, provider, prompt: str, *, timeout_seconds: float = 5.0):
        incoming = Request(prompt, timeout_seconds=timeout_seconds)
        if not self._semaphore.acquire(blocking=False):
            raise InferenceFailure("Inference capacity reached")
        try:
            future = self._executor.submit(
                generate, provider, incoming.prompt, timeout_seconds=incoming.timeout_seconds
            )
        except BaseException:
            self._semaphore.release()
            raise
        future.add_done_callback(lambda completed: self._semaphore.release())
        try:
            return await asyncio.wait_for(asyncio.wrap_future(future), timeout=incoming.timeout_seconds)
        except (TimeoutError, asyncio.TimeoutError) as exc:
            raise InferenceTimeout("Inference timed out") from exc

    def shutdown(self):
        self._executor.shutdown(wait=False, cancel_futures=False)
