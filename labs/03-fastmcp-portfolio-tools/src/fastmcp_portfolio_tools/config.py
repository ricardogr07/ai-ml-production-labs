from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    service_name: str = "fastmcp-portfolio-tools"
    service_version: str = "0.1.0"
    mcp_auth_token: str | None = None
    rate_limit_calls: int = 60
    rate_limit_period: int = 60
    port: int = 8080
