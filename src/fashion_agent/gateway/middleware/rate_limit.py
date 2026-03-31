"""Simple in-memory rate limiter and concurrency control middleware."""

from __future__ import annotations

import asyncio
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from fashion_agent.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter + concurrent request limiter.

    Args:
        max_concurrent: max simultaneous requests (0 = unlimited)
        requests_per_second: sustained request rate limit (0 = unlimited)
    """

    def __init__(self, app, max_concurrent: int = 20, requests_per_second: float = 50):
        super().__init__(app)
        self._semaphore = asyncio.Semaphore(max_concurrent) if max_concurrent > 0 else None
        self._rps = requests_per_second
        self._tokens = float(requests_per_second)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def _try_acquire(self) -> bool:
        if self._rps <= 0:
            return True
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._rps, self._tokens + elapsed * self._rps)
            self._last_refill = now
            if self._tokens >= 1:
                self._tokens -= 1
                return True
            return False

    async def dispatch(self, request: Request, call_next):
        if not await self._try_acquire():
            logger.warning("rate_limited", path=request.url.path)
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limited", "detail": "Too many requests"},
            )

        if self._semaphore:
            try:
                acquired = self._semaphore._value > 0  # noqa: SLF001
                if not acquired:
                    logger.warning("concurrency_limited", path=request.url.path)
                    return JSONResponse(
                        status_code=503,
                        content={
                            "error": "service_busy",
                            "detail": "Too many concurrent requests",
                        },
                    )
                async with self._semaphore:
                    return await call_next(request)
            except Exception:
                return await call_next(request)

        return await call_next(request)
