"""
Minimal in-memory rate limiter.

This is a single small EC2 instance with no auth and no shared cache — a
per-process, per-IP sliding window is enough to blunt accidental or
malicious request floods without adding a Redis dependency. It resets on
every process restart, which is fine for this use case.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from backend.app.core.config import settings

# client_ip -> timestamps of recent requests, per limiter name
_hits: Dict[str, Dict[str, Deque[float]]] = defaultdict(lambda: defaultdict(deque))


def _client_ip(request: Request) -> str:
    # Trust X-Forwarded-For since nginx sits in front of uvicorn (see
    # proxy_set_header X-Real-IP in the nginx config) — fall back to the
    # direct peer address if it's ever missing.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, per_minute: int | None = None):
    """FastAPI dependency factory: limits each client IP to N requests/min
    per named bucket (e.g. "ingest", "query") so one endpoint's traffic
    doesn't eat another's budget."""

    limit = per_minute or settings.rate_limit_per_minute

    async def _check(request: Request) -> None:
        ip = _client_ip(request)
        now = time.monotonic()
        window = _hits[name][ip]

        while window and now - window[0] > 60:
            window.popleft()

        if len(window) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({limit}/min for {name}). Try again shortly.",
            )

        window.append(now)

    return _check
