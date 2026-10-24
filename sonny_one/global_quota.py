"""Conservative in-process global quota for private inference.

This is defense in depth for a single process, not a guarantee against
provider charges or multi-worker traffic. External quota/billing controls
and a shared counter are mandatory before public deployment.
"""
from threading import Lock
from time import monotonic


class GlobalRequestQuota:
    def __init__(self, max_requests: int = 100):
        if isinstance(max_requests, bool) or not isinstance(max_requests, int) or not 1 <= max_requests <= 10000:
            raise ValueError("Invalid global quota")
        self._limit = max_requests
        self._used = 0
        self._lock = Lock()

    def allow(self) -> bool:
        with self._lock:
            if self._used >= self._limit:
                return False
            self._used += 1
            return True

    @property
    def remaining(self) -> int:
        with self._lock:
            return self._limit - self._used
