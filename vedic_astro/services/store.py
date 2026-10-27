"""Small key/value stores with TTL used for chat history and chart context.

``MemoryStore`` is process-local (fine for development and single-worker
deployments). ``RedisStore`` makes state shared across workers and restarts.
"""

from __future__ import annotations

import json
import threading
import time
from collections import OrderedDict
from typing import Any, Protocol


class Store(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int) -> None: ...
    def delete(self, key: str) -> None: ...


class MemoryStore:
    """Thread-safe in-memory store with per-key TTL and a bounded size."""

    def __init__(self, max_entries: int = 5000, clock=time.monotonic) -> None:
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_entries
        self._clock = clock

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if expires < self._clock():
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._data[key] = (self._clock() + ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max:
                self._data.popitem(last=False)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


class RedisStore:
    """JSON-serialising Redis store. Requires the ``redis`` package."""

    def __init__(self, url: str, prefix: str = "vedic:") -> None:
        import redis

        self._client = redis.Redis.from_url(url, decode_responses=True)
        self._prefix = prefix

    def get(self, key: str) -> Any | None:
        raw = self._client.get(self._prefix + key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._client.set(self._prefix + key, json.dumps(value), ex=ttl)

    def delete(self, key: str) -> None:
        self._client.delete(self._prefix + key)


def build_store(redis_url: str | None) -> Store:
    return RedisStore(redis_url) if redis_url else MemoryStore()
