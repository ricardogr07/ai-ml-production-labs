from __future__ import annotations

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    service_name: str = "fastapi-azure-ml-service"
    service_version: str = "0.1.0"


settings = Settings()
