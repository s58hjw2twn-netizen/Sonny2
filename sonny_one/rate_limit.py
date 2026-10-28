"""In-process sliding-window limiter for local prototype inference.

Not a distributed production rate limiter. Restarts clear counters; multiple
workers do not share state. Use an external shared limiter before deployment.
"""
from collections import deque
from threading import Lock
from time import monotonic
import math


class LocalRateLimiter:
    def __init__(self, limit: int = 30, window_seconds: float = 60, max_identities: int = 10000):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Invalid rate limit")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) or not math.isfinite(window_seconds) or not 0 < window_seconds <= 3600:
            raise ValueError("Invalid rate window")
        if isinstance(max_identities, bool) or not isinstance(max_identities, int) or max_identities < 1:
            raise ValueError("Invalid identity capacity")
        self.max_identities = max_identities
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._hits = {}

    def allow(self, identity: str) -> bool:
        if not isinstance(identity, str) or not identity or len(identity) > 256:
            return False
        now = monotonic()
        with self._lock:
            if identity not in self._hits and len(self._hits) >= self.max_identities:
                expired = [key for key, values in self._hits.items() if not values or values[-1] <= now - self.window_seconds]
                for key in expired:
                    del self._hits[key]
                if len(self._hits) >= self.max_identities:
                    return False
            hits = self._hits.setdefault(identity, deque())
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True
