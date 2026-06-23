"""Per-IP sliding-window rate limiter for the FastMCP HTTP transport."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, period: int = 60) -> None:
        super().__init__(app)
        self._calls = calls
        self._period = period
        self._log: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        now = time.monotonic()
        cutoff = now - self._period
        self._log[ip] = [t for t in self._log[ip] if t > cutoff]
        if len(self._log[ip]) >= self._calls:
            return JSONResponse({"error": "rate limit exceeded"}, status_code=429)
        self._log[ip].append(now)
        return await call_next(request)
