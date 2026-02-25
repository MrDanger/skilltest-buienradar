from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "Zypp Dutch Weather Analysis"
    buienradar_url: str = Field(
        default="https://data.buienradar.nl/2.0/feed/json",
        description="Buienradar JSON endpoint",
    )
    request_timeout_seconds: float = 15.0
    scheduler_default_interval_minutes: int = 20
    database_path: str = "data/weather.sqlite"

    model_config = SettingsConfigDict(
        env_prefix="WEATHER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        path = Path(self.database_path)
        if not path.is_absolute():
            root = Path(__file__).resolve().parents[2]
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"


def get_settings() -> Settings:
    return Settings()
