from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    service_name: str = "fastmcp-portfolio-tools"
    service_version: str = "0.1.0"
