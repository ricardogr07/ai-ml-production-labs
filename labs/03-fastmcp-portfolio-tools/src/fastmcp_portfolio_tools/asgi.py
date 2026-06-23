"""ASGI entrypoint: FastMCP HTTP app with rate limiting middleware."""

from __future__ import annotations

from starlette.middleware import Middleware

from fastmcp_portfolio_tools.middleware import RateLimitMiddleware
from fastmcp_portfolio_tools.server import _settings, mcp

app = mcp.http_app(
    transport="streamable-http",
    middleware=[
        Middleware(
            RateLimitMiddleware,
            calls=_settings.rate_limit_calls,
            period=_settings.rate_limit_period,
        ),
    ],
)
