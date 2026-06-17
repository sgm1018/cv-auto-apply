"""In-memory token bucket rate limiter with optional daily cap."""
import time
from collections import deque
from dataclasses import dataclass, field

from cvapplier.utils.time import utcnow


@dataclass
class _Bucket:
    tokens: float
    last_refill: float
    daily_window: deque = field(default_factory=deque)


class TokenBucketRateLimiter:
    """In-memory token bucket. v1: single-process."""

    def __init__(self, *, rate_per_min: int, burst: int, daily_limit: int | None = None) -> None:
        self.capacity = float(burst)
        self.refill_per_sec = rate_per_min / 60.0
        self.daily_limit = daily_limit
        self._buckets: dict[str, _Bucket] = {}

    def _bucket(self, key: str) -> _Bucket:
        b = self._buckets.get(key)
        if b is None:
            b = _Bucket(tokens=self.capacity, last_refill=time.monotonic())
            self._buckets[key] = b
        return b

    def _refill(self, b: _Bucket) -> None:
        now = time.monotonic()
        b.tokens = min(self.capacity, b.tokens + (now - b.last_refill) * self.refill_per_sec)
        b.last_refill = now

    async def allow(self, key: str, *, n: int = 1) -> bool:
        if self.daily_limit is not None:
            cutoff = utcnow().timestamp() - 86400
            b = self._bucket(key)
            while b.daily_window and b.daily_window[0] < cutoff:
                b.daily_window.popleft()
            if len(b.daily_window) + n > self.daily_limit:
                return False
        b = self._bucket(key)
        self._refill(b)
        if b.tokens >= n:
            b.tokens -= n
            if self.daily_limit is not None:
                for _ in range(n):
                    b.daily_window.append(utcnow().timestamp())
            return True
        return False
