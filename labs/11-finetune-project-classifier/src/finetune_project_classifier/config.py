from pathlib import Path

from pydantic_settings import SettingsConfigDict

from production_labs_shared.config import BaseLabSettings


class Settings(BaseLabSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).resolve().parents[2] / ".env"), extra="ignore"
    )
    model_dir: Path = Path("artifacts/project-classifier")
    base_model: str = "distilbert-base-uncased"


settings = Settings()
