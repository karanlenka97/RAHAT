"""Idempotency Management for Offline-First Sync Replays in RAHAT."""
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any


class IdempotencyCache:
    """Thread-safe in-memory idempotency cache with TTL expiration."""

    def __init__(self, ttl_seconds: int = 86400):
        self._ttl = timedelta(seconds=ttl_seconds)
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve stored response payload if key exists and has not expired."""
        if not key:
            return None
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if datetime.now(timezone.utc) > entry["expires_at"]:
                del self._store[key]
                return None
            return entry["response_data"]

    def set(self, key: str, response_data: Any) -> None:
        """Store response data associated with an idempotency key."""
        if not key:
            return
        with self._lock:
            self._store[key] = {
                "response_data": response_data,
                "expires_at": datetime.now(timezone.utc) + self._ttl,
                "created_at": datetime.now(timezone.utc),
            }

    def clear(self) -> None:
        """Clear all cached idempotency keys (useful for testing)."""
        with self._lock:
            self._store.clear()


# Global singleton instance for API request deduplication
idempotency_cache = IdempotencyCache()
