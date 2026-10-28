"""In-process admission control for local inference concurrency.

Limits simultaneous callers, not surviving provider threads after timeout.
A shared multi-worker quota and provider-side hard limits are required for production.
"""
from threading import BoundedSemaphore


class LocalConcurrencyGate:
    def __init__(self, max_active: int = 4):
        if isinstance(max_active, bool) or not isinstance(max_active, int) or max_active < 1 or max_active > 128:
            raise ValueError("Invalid concurrency capacity")
        self._slots = BoundedSemaphore(max_active)

    def acquire(self) -> bool:
        return self._slots.acquire(blocking=False)

    def release(self) -> None:
        self._slots.release()
