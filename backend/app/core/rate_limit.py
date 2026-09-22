"""
Small in-memory sliding-window rate limiter.

Purpose: stop a single visitor (or a script) from running up your Azure bill.
It is per-process, which is fine for one App Service / Container Apps instance.
If you scale out to several instances, move the counters to Azure Cache for
Redis (same interface, swap the storage) or enforce limits in Front Door / API
Management.
"""
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

from app.config import settings

_WINDOW_SECONDS = 60.0
_hits: dict[str, deque] = {}
_lock = threading.Lock()
_last_prune = 0.0


def _client_key(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check(key: str, limit: int, now: float | None = None) -> tuple[bool, int]:
    """Record a hit for `key`. Returns (allowed, retry_after_seconds)."""
    global _last_prune
    now = time.monotonic() if now is None else now
    with _lock:
        window = _hits.setdefault(key, deque())
        cutoff = now - _WINDOW_SECONDS
        while window and window[0] <= cutoff:
            window.popleft()

        allowed = len(window) < limit
        retry_after = 0
        if allowed:
            window.append(now)
        else:
            retry_after = max(1, int(window[0] + _WINDOW_SECONDS - now) + 1)

        # Occasionally drop idle keys so the dict cannot grow forever.
        if now - _last_prune > _WINDOW_SECONDS:
            _last_prune = now
            for k in [k for k, v in _hits.items() if not v or v[-1] <= cutoff]:
                _hits.pop(k, None)

        return allowed, retry_after


def reset() -> None:
    """Clear all counters (used by tests)."""
    with _lock:
        _hits.clear()


def rate_limited(request: Request) -> None:
    """FastAPI dependency: raise 429 when the caller is over the limit."""
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return
    allowed, retry_after = check(_client_key(request), limit)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(retry_after)},
        )
