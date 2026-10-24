"""In-process sliding-window limiter for local prototype inference.

Not a distributed production rate limiter. Restarts clear counters; multiple
workers do not share state. Use an external shared limiter before deployment.
"""
from collections import deque
from threading import Lock
from time import monotonic


class LocalRateLimiter:
    def __init__(self, limit: int = 30, window_seconds: float = 60):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Invalid rate limit")
        if isinstance(window_seconds, bool) or not isinstance(window_seconds, (int, float)) or not 0 < window_seconds <= 3600:
            raise ValueError("Invalid rate window")
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._hits = {}

    def allow(self, identity: str) -> bool:
        if not isinstance(identity, str) or not identity or len(identity) > 256:
            return False
        now = monotonic()
        with self._lock:
            hits = self._hits.setdefault(identity, deque())
            while hits and hits[0] <= now - self.window_seconds:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True
